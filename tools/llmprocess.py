""" 
Main class for processing data with LLMs.

The process will read in a csv table with clausing pairs and generate a prompt for each pair to ask for the sequencing class, linkage word and reasoning.
The prompt will be sent to the LLM API and the response will be saved to a file. 
Sequencing class, linkage words, and resaoning will be appended to the table and saved to a csv file.

Input:
- csv table with clausing pairs
- filename for instruction txt file for prompt generation
- filename for example excel/json file to include in prompt
- filename for excel/json file with sequencing class definitions to include in prompt
- output path of results csv file and prompt/response txt files

"""

import os
import json
import pandas as pd
import numpy as np
import json
import argparse

from load_schema_json import load_json, validate_json, json_to_dataframe
from excel_json_converter import excel_to_json
#import importlib
#importlib.reload(utils_llm)
from utils_llm import LLM


def load_text(filename):
    """
    Load text from a file.

    Parameters:
    -----------
    - filename (str): The filename of the text to load.

    Returns:
    --------
    - text (str): The text.
    """

    with open(filename, 'r') as f:
        text = f.read()
    return text

def save_text(text, filename):
    """
    Save text to a file.
    """
    with open(filename, 'w') as f:
        f.write(text)



def merge_definitions_examples(definitions, example_subset, linkage_subset):
    """
    Merge the class definitions with the example subset and linkage subset.

    Parameters:
    -----------
    - definitions (dict): The definitions for the prompt.
    - example_subset (list): The subset of examples to use for the prompt.
    - linkage_subset (list): The subset of linkage words corresponding to the examples.

    Returns:
    --------
    - result_str (str): The class definitions inluding examples and linkage words as a string.

    """
    class_str = ""

    for definition in definitions['Sequencing_Types']:
        class_str += f"{definition['Type']}\n"
        for subtype in definition['Subtypes']:
            class_str += f"\t{subtype['Subtype']}\n"
            for subsubtype in subtype['Sub_Subtypes']:
                class_str += f"\t\t{subsubtype['Sub_Subtype']}\n"
                class_str += f"\t\t\t{subsubtype['Definition']}\n"
                class_str += f"\t\t\tExamples:\n"
                # find example subset for this subsubtype
                example_subset = [example for example in example_subset if example['Sub_Subtype'] == subsubtype['Sub_Subtype']]
                linkage_subset = [linkage for linkage in linkage_subset if linkage['Sub_Subtype'] == subsubtype['Sub_Subtype']]
                for example, linkage in zip(example_subset, linkage_subset):
                    class_str += f"\t\t\t\t{example['Example']}\n"
                    class_str += f"\t\t\t\t\t{linkage['Linkage_Word']}\n"
                class_str += "\n"
            class_str += "\n"
        class_str += "\n"

    return class_str



class LLMProcess():
    """
    Main class for processing data with LLMs.

    The process will read in a csv table with clausing pairs and generate a prompt for each pair to ask for the sequencing class, linkage word and reasoning.
    The prompt will be sent to the LLM API and the response will be saved to a file. 
    Sequencing class, linkage words, and resaoning will be appended to the table and saved to a csv file.

    This LLM process pipeline includes the following main steps:
    - load and and pre-process examples, sequencing definitions, instruction prompts 
    - load clausing pairs
    - generate prompt string
    - call OpenAI API
    - save prompt and response to file
    - save results to csv file

    Input:
    - csv table with clausing pairs
    - filename for instruction txt file for prompt generation
    - fileanme for example excel/json file to include in prompt
    - filename for excel/json file with sequencing class definitions to include in prompt
    - output path of results csv file and prompt/response txt files
    """

    def __init__(self, filename_pairs, filename_examples, filename_definitions, filename_zero_prompt, outpath, modelname_llm):
        """
        Initialize LLMProcess class.

        Parameters:
        -----------
        - filename_pairs (str): The filename of the csv table with clausing pairs.
        - filename_examples (str): The filename of the examples json file.
        - filename_definitions (str): The filename of the definitions json file.
        - filename_zero_prompt (str): The filename of the zero-shot instruction prompt text file.
        - outpath (str): The path to the output folder.
        - modelname_llm (str): The name of the LLM model to use.

        """
        # Check if filename_examples is excel file
        if filename_examples.endswith(".xlsx"):
            # convert filename_examples to json
            json_filename_out = filename_examples.replace(".xlsx", "_converted.json")
            excel_to_json(filename_examples, json_filename_out)
            filename_examples = json_filename_out

        # Check if filename_definitions is excel file
        if filename_definitions.endswith(".xlsx"):
            # convert filename_definitions to json
            json_filename_out = filename_definitions.replace(".xlsx", "_converted.json")
            excel_to_json(filename_definitions, json_filename_out))
            filename_definitions = json_filename_out


        self.filename_pairs = filename_pairs
        self.filename_examples = filename_examples
        self.filename_definitions = filename_definitions
        self.filename_zero_prompt = filename_zero_prompt
        os.makedirs(outpath, exist_ok=True)
        self.outpath = outpath
        self.modelname_llm = modelname_llm

        # load examples from json file
        examples = load_json(self.filename_examples)
        #self.schema = load_json(self.filename_schema)
        #assert validate_json(self.examples, self.schema)
        self.df_examples = json_to_dataframe(examples)

        # load clausing pairs
        self.df_pairs = pd.read_csv(self.filename_pairs)

        # Select examples for each type
        self.example_types = self.df_examples['Sub_Subtype'].unique()

        # get first three letter characters of example types and write in captial letters
        self.example_types_short = [example_type[:3].upper() for example_type in self.example_types]

        # load sequencing_classes, sequencing_definition
        self.get_sequencing_classes(self.filename_definitions)

        # generate main part of prompt consisting of instructions, definitions, and examples
        self.preprocess_prompt()

        # initialize token_counter
        self.token_count = 0

        # initiate results dataframe
        self.df_res = self.df_pairs.copy()
        self.df_res['pred_class'] = np.nan
        self.df_res['pred_class_prob'] = np.nan
        self.df_res['pred_linkage'] = np.nan
        self.df_res['prompt_id'] = np.nan
        self.df_res['filename_prompt'] = np.nan
        self.df_res['filename_response'] = np.nan
        self.df_res['tokens'] = np.nan
        self.df_res['modelname_llm'] = np.nan
        self.df_res['reasoning'] = np.nan

        # Initiate LLM with API key
        self.llm = LLM(filename_openai_key=None, model_name = self.modelname_llm)


    def preprocess_prompt(self):
        # generate main part of prompt consisting of instructions, definitions, and examples
        example_string = """ """
        for index, row in self.examples.iterrows():
            clause1 = row['Linked_Chunk_1']
            clause2 = row['Linked_Chunk_2']
            text = row['Example']
            # f
            example_string += f"""Input\nText content: {row['Example']}\n"""
            example_string += f"""Clause 1: {row['Linked_Chunk_1']}\n"""
            example_string += f"""Clause 2: {row['Linked_Chunk_2']}\n"""
            example_string += f"""\nAnswer\nClassification: {row['Sub_Subtype']}\n"""
            example_string += f"""Linkage word: {row['Linkage_Word']}\n"""
            example_string += f"""Reason: {row['Reasoning']}\n"""
            example_string += f"""\n"""

        # replace example_types with example_types_short in example_string
        for example_type, example_type_short in zip(self.example_types, self.example_types_short):
            example_string = example_string.replace(example_type, example_type_short)

        self.zero_shot_prompt = self.zero_shot_prompt.replace('EXAMPLES', example_string)

        # add definitions to main_prompt
        self.zero_shot_prompt = self.zero_shot_prompt.replace('SEQUENCING_CLASSES', self.sequencing_classes)
        self.zero_shot_prompt = self.zero_shot_prompt.replace('DESCRIPTION_CLASSES', self.sequencing_definition)


    def get_sequencing_classes(self, filename_definitions):
        definitions = load_json(filename_definitions)
        self.sequencing_definition = json.dumps(definitions, indent=2)
        # find all sub_subtypes in definitions
        sub_subtypes = []
        for definition in definitions['Sequencing_Types']:
            for subtype in definition['Subtypes']:
                for subsubtype in subtype['Sub_Subtypes']:
                    # add subsubtype to list if not already in list
                    if subsubtype['Sub_Subtype'] not in sub_subtypes:
                        sub_subtypes.append(subsubtype['Sub_Subtype'])
        sequencing_classes = sub_subtypes

        # add also a three letter characters and write in captial letters
        self.seq_classes = [seq_class[:3].upper() for seq_class in sequencing_classes]

        # convert list to string
        self.sequencing_classes = ', '.join(f"'{item}'" for item in sequencing_classes)

        # generate subdirectory for saving all prompt and response files
        self.outpath_prompts = os.path.join(self.outpath, 'prompts_responses')
        os.makedirs(self.outpath_prompts, exist_ok=True)


    def run(self):

        # path to results
        self.fname_results = os.path.join(self.outpath, 'results.csv')

        for index, row in self.df_pairs.iterrows():
            # get text content
            text_content = row['Text_Content']
            # get text chunks
            text_chunk_1 = row['clause_1']
            text_chunk_1 = row['clause_2']

            self.prompt = self.zero_shot_prompt.copy()
            self.prompt = self.prompt.replace('TEXT_CONTENT', text_content)
            self.prompt = self.prompt.replace('CHUNK_1', text_chunk_1)
            self.prompt = self.prompt.replace('CHUNK_2', text_chunk_2)

            # call OPenAi API with prompt
            completion_text, tokens_used, chat_id, logprobs = self.llm.request_completion(self.prompt, max_tokens = 300)
            # for gpt-4:
            #completion_text, tokens_used, chat_id, message_response = llm.request_chatcompletion(prompt, max_tokens = 300)
            #logprobs = None

            # tokens_used
            self.token_count += self.tokens_used

            # save prompt to file
            filename_prompt = f'prompt_{chat_id}.txt'
            save_text(self.prompt, os.path.join(self.outpath_prompts, filename_prompt))

            # save response to file
            filename_response = f'response_{chat_id}.txt'
            save_text(completion_text, os.path.join(self.outpath_prompts, filename_response))

            if completion_text.startswith('\n'):
                completion_text = completion_text[1:]

            # check if there are 3 lines in completion_text
            if len(completion_text.split('\n')) == 3:
                # class of test sample
                try:
                    class_predicted = completion_text.split('\n')[0].split(':')[1].strip()
                except:
                    print('WARNING: completion_text not correct format! Skipping test sample')
                    print(completion_text)
                    completion_text = completion_text.split('\n')[0]
                # linkage word of test sample
                try:
                    linkage_predicted = completion_text.split('\n')[1].split(':')[1].strip()
                except:
                    print('WARNING: completion_text not correct format for linkage word!')
                    print(completion_text)
                    linkage_predicted = 'NA'

                # get reasoning
                try:
                    reasoning = completion_text.split('\n')[2].split(':')[1].strip()
                except:
                    print('WARNING: completion_text not correct format for reasoning!')
                    print(completion_text)
                    reasoning = 'NA'

                # probability of predicted class
                if logprobs is not None:
                    class_prob = logprobs[3]
                else:
                    class_prob = 0
            elif (len(completion_text.split('\n')) == 2) and completion_text.split('\n')[0].startswith('classification'):
                print('WARNING: completion_text has only 2 lines! Skipping reasoning')
                try:
                    class_predicted = completion_text.split('\n')[0].split(':')[1].strip()
                except:
                    print('WARNING: completion_text not correct format! Skipping test sample')
                    print(completion_text)
                    completion_text = completion_text.split('\n')[0]
                try:
                    linkage_predicted = completion_text.split('\n')[1].split(':')[1].strip()
                except:
                    print('WARNING: completion_text not correct format for linkage word!')
                    linkage_predicted = 'NA'
                reasoning = 'NA'
                if logprobs is not None:
                    class_prob = logprobs[3]
                else:
                    class_prob = 0
            else:
                print('WARNING: completion_text has not not enough lines!')
                print(completion_text)
                class_predicted = 'NA'
                linkage_predicted = 'NA'
                reasoning = 'NA'
                class_prob = 0

            class_prob = round(np.exp(class_prob),3)
            
            # add results to dataframe
            self.df_res.loc[index, 'pred_class'] = class_predicted
            self.df_res.loc[index, 'pred_class_prob'] = class_prob
            self.df_res.loc[index, 'pred_linkage'] = linkage_predicted
            self.df_res.loc[index, 'prompt_id'] = chat_id
            self.df_res.loc[index, 'filename_prompt'] = filename_prompt
            self.df_res.loc[index, 'filename_response'] = filename_response
            self.df_res.loc[index, 'tokens'] = tokens_used
            self.df_res.loc[index, 'modelname_llm'] = self.modelname_llm
            self.df_res.loc[index, 'reasoning'] = reasoning

            # save intermediate results to disk
            self.df_res.to_csv(self.fname_results, index=False)

            #print results
            print(f'Index: {index} | Prediction: {class_predicted} | Probability: {class_prob} | Used tokens: {tokens_used} ')

        # Write token count to file
        filename_token_count = f'token_count_{self.modelname_llm}.txt'
        save_text(str(self.token_count), os.path.join(self.outpath, filename_token_count))

        print(f'Experiment finished! Results saved to folder {self.outpath}')



if __name__ == "__main__":
    # get arguments from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--outpath', type=str, default="../results/", help='The path to the output folder.', required=False)
    parser.add_argument('--filename_pairs', type=str, default="../data/sequencing_pairs.csv", help='The filename of the csv table with clausing pairs.', required=False)
    parser.add_argument('--filename_examples', type=str, default="sequencing_examples_reason.json", help='The path+filename of the examples json file.', required=False)
    parser.add_argument('--filename_definitions', type=str, default="sequencing_types.json", help='The path+filename of the definitions json file.', required=False)
    parser.add_argument('--filename_zero_prompt', type=str, default="instruction_prompt.txt", help='The path+filename of the zero-shot instruction prompt text file.', required=False)
    parser.add_argument('--modelname_llm', type=str, default='gpt-3.5-turbo-instruct', help='The name of the LLM model to use.', required=False)
    args = parser.parse_args()

    # run experiment pipeline
    llm_process = LLMProcess(filename_pairs = args.filename_pairs,
                            filename_examples = args.filename_examples,
                            filename_definitions = args.filename_definitions,
                            filename_zero_prompt = args.filename_zero_prompt,
                            outpath = args.outpath,
                            modelname_llm = args.modelname_llm)
    llm_process.run()