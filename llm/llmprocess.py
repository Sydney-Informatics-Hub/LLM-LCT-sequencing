""" 
Process for sequencing classification and reasoning with LLM.

The LLM process will read in a csv table with clausing pairs and generate a prompt for each pair to ask for the sequencing class, linkage word and reasoning.
The prompt will be send to the LLM and the response will be saved to a file. 
Sequencing class, linkage words, and reasoning will be appended to the table and saved to a csv file.

Input:
- csv table with clausing pairs
- text filename
- filename for instruction txt file for prompt generation
- filename for example excel/json file to include in prompt
- filename for excel/json file with sequencing class definitions to include in prompt
- output path of results csv file and prompt/response txt files

The results csv includes at least the following columns needed for the annotation tool:
sequence_id,c1_start, c1_end, c2_start,c2_end, linkage_words, predicted_classes, reasoning, confidence, window_start, window_end

in addition, the following columns are added:
prompt_id, filename_prompt, filename_response, tokens, modelname_llm

"""

import os
import pandas as pd
import numpy as np
import json
import argparse
from enum import Enum
import logging

from .load_schema_json import load_json, json_to_dataframe
from .excel_json_converter import excel_to_json
from .utils_llm import LLM


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


class LCTclasses(Enum):
    """
    Enum for LCT classes.
    """
    NA = 0
    INT = 1
    SUB = 2
    CON = 3
    SEQ = 4
    REI = 5
    REP = 6
    COH = 7
    INC = 8

def lct_string_to_int(s):
    """
    Convert LCT sequence string to integer.
    """
    result = getattr(LCTclasses, s, None)
    if result is None:
        logging.debug(f"'{s}' does not correspond to any known Classification.")
        logging.debug(f"Need to be one of {list(LCTclasses.__members__.keys())}")
        return None
    else:
        return result.value


class LLMProcess():
    """
    Main class for processing data with LLMs.

    The process will read in a csv table with clausing pairs and generate a prompt for each pair to ask for the sequencing class, linkage word and reasoning.
    The prompt will be sent to the LLM API and the response will be saved to a file. 
    Sequencing class, linkage words, and resaoning will be appended to the table and saved to a csv file.

    This LLM process pipeline includes the following main steps:
    - load and pre-process examples, sequencing definitions, instruction prompts
    - load clausing pairs
    - generate prompt string
    - call OpenAI API
    - save prompt and response to file
    - save results to csv file

    Input:
    - csv table with clausing pairs
    - text filename
    - filename for instruction txt file for prompt generation
    - fileanme for example excel/json file to include in prompt
    - filename for excel/json file with sequencing class definitions to include in prompt
    - output path of results csv file and prompt/response txt files
    """

    def __init__(self, 
                 filename_pairs, 
                 filename_text,
                 filename_examples, 
                 filename_definitions="../schemas/sequencing_types.xlsx",
                 filename_zero_prompt="../schemas/instruction_prompt.txt",
                 outpath="../results_llm/",
                 modelname_llm="gpt-3.5-turbo-instruct"):
        """
        Initialize LLMProcess class.

        Parameters:
        -----------
        - filename_pairs (str): The filename of the csv table with clausing pairs.
        - filename_text (str): The filename of the text file with the text to be claused.
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
            excel_to_json(filename_definitions, json_filename_out)
            filename_definitions = json_filename_out

        self.filename_pairs = filename_pairs
        self.filename_text = filename_text
        self.filename_examples = filename_examples
        self.filename_definitions = filename_definitions
        self.filename_zero_prompt = filename_zero_prompt
        self.outpath = outpath
        self.modelname_llm = modelname_llm

        # check if outpath includes a folder that starts with string 'results'
        # if so, add 1 to the number of the folder
        # if not, create folder 'results1'
        os.makedirs(outpath, exist_ok=True)
        list_folders = os.listdir(outpath)
        list_exp_folders = [folder for folder in list_folders if folder.startswith('results')]
        if len(list_exp_folders) == 0:
            outpath = os.path.join(outpath, 'results1')
        else:
            exp_folder_numbers = [int(folder[7:]) for folder in list_exp_folders]
            exp_folder_numbers.sort()
            last_exp_folder_number = exp_folder_numbers[-1]
            outpath = os.path.join(outpath, f'results{last_exp_folder_number+1}')
        os.makedirs(outpath, exist_ok=True)
        self.outpath = outpath

        # load examples from json file
        examples = load_json(self.filename_examples)
        # self.schema = load_json(self.filename_schema)
        # assert validate_json(self.examples, self.schema)
        self.df_examples = json_to_dataframe(examples)

        # load clausing pairs
        self.df_sequences = pd.read_csv(self.filename_pairs)

        # Select examples for each type
        self.example_types = self.df_examples['Sub_Subtype'].unique()

        # get first three letter characters of example types and write in captial letters
        self.example_types_short = [example_type[:3].upper() for example_type in self.example_types]

        # get instructions
        self.zero_shot_prompt = load_text(self.filename_zero_prompt)

        # initialize token_counter
        self.token_count = 0

        # initiate results dataframe
        self.df_res = self.df_sequences.copy()
        self.df_res['predicted_classes'] = None
        self.df_res['predicted_classes_name'] = None
        self.df_res['confidence'] = np.nan
        self.df_res['linkage_words'] = None
        self.df_res['window_start'] =None
        self.df_res['window_end'] = None
        self.df_res['prompt_id'] = None
        self.df_res['filename_prompt'] = None
        self.df_res['filename_response'] = None
        self.df_res['tokens'] = None
        self.df_res['modelname_llm'] = None
        self.df_res['reasoning'] = None

    def estimate_compute_cost(self, 
                              path_cost = '../schemas/openai_pricing.json',
                              avg_token_input = 2700,
                              avg_token_output = 450,
                              avg_time = 1.31):
        """
        Estimate compute resources:
            - the costs for the LLM process.
            - the compute time for the LLM process.

        Parameters:
        -----------
        - path_cost (str): The path to the cost schema (incl costs in $/1k token)
        - avg_token_input (int): The average number of tokens needed for the input.
        - avg_token_output (int): The average number of tokens needed for the output.
        - avg_time (float): The average time in seconds needed for the LLM process.

        Returns:
        --------
        - cost_estimate (dict): A dictionary with the estimated compute resources.
        """
        # load cost schema
        cost_schema = load_json(path_cost)
        ntokens_in = len(self.df_examples) * avg_token_input / 1000
        ntokens_out= len(self.df_examples) * avg_token_output / 1000
        compute_time = len(self.df_examples) * avg_time


        # check if modelname_llm is in cost_schema
        if self.modelname_llm not in cost_schema.keys():
            logging.warning(f'WARNING: {self.modelname_llm} not in cost_schema!')
            costs = None
        else:
            modelcost = cost_schema['self.modelname_llm']
            # check if modelcost includes "input" and "output"
            if 'input' in modelcost.keys() and 'output' in modelcost.keys():
                costs = modelcost['input'] * avg_token_input + modelcost['output'] * avg_token_output

            elif 'input_usage' in modelcost.keys() and 'output_usage' in modelcost.keys():
                costs = modelcost['input_usage'] * avg_token_input + modelcost['output_usage'] * avg_token_output
            else:
                logging.warning('WARNING: modelcost does not include "input" or "output"!')
                costs = None

        cost_estimate = {'compute_time': compute_time,
                         'costs': costs}
        
        return cost_estimate


    def preprocess_prompt(self):
        # generate main part of prompt consisting of instructions, definitions, and examples
        example_string = """ """
        for index, row in self.df_examples.iterrows():
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

    def get_text_chunks(self, fname_text, c1_start, c1_end, c2_start, c2_end, window_start, window_end):
        """
        get text for two clauses with idx_start and idx_end.

        Parameters:
        -----------
        - fname_text (str): The filename of the text file with the text to be claused.
        - c1_start (int): The start index of clause 1.
        - c1_end (int): The end index of clause 1.
        - c2_start (int): The start index of clause 2.
        - c2_end (int): The end index of clause 2.
        - window_start (int): The start index of the window.
        - window_end (int): The end index of the window.

        Returns:
        --------
        - text_chunk_1 (str): The text of clause 1.
        - text_chunk_2 (str): The text of clause 2.
        - text_content (str): The text content of the whole text between c1_start and c2_end.
        """
        # read text file and encode to utf-8
        text = load_text(fname_text)
        text = text.encode('utf-8').decode('utf-8')
        # get text content
        text_content = text[window_start:window_end]
        # get text chunks
        text_chunk_1 = text[c1_start:c1_end]
        text_chunk_2 = text[c2_start:c2_end]
        return text_chunk_1, text_chunk_2, text_content

    def run(self, filename_openai_key=None):
        """
        Run the LLM process pipeline for each clausing pair

        Parameters:
        -----------
        - filename_openai_key (str): The filename of the OpenAI key file. 
            If None provided, openai.api_key need to be set manually beforehand.
        
        """
        # load sequencing_classes, sequencing_definition
        self.get_sequencing_classes(self.filename_definitions)

        # generate main part of prompt consisting of instructions, definitions, and examples
        self.preprocess_prompt()

        # Initiate LLM with API key
        self.llm = LLM(filename_openai_key, model_name = self.modelname_llm)

        # path to results
        self.fname_results = os.path.join(self.outpath, 'results.csv')

        for index, row in self.df_sequences.iterrows():
             # get text content and clauses 
            # Set context window for now to all context between c1 and c2
            window_start = row['c1_start']
            window_end = row['c2_end']
            text_chunk_1, text_chunk_2, text_content = self.get_text_chunks(self.filename_text, 
                                                                            row['c1_start'], 
                                                                            row['c1_end'],
                                                                            row['c2_start'],
                                                                            row['c2_end'],
                                                                            window_start,
                                                                            window_end)
            
            logging.debug(f"Clauses for index {index}:")
            logging.debug("text1:", text_chunk_1)
            logging.debug("text2:", text_chunk_2)
           
            # copy string self.zero_shot_prompt
            self.prompt = self.zero_shot_prompt
            self.prompt = self.prompt.replace('TEXT_CONTENT', text_content)
            self.prompt = self.prompt.replace('CHUNK_1', text_chunk_1)
            self.prompt = self.prompt.replace('CHUNK_2', text_chunk_2)

            # call OPenAi API with prompt
            completion_text, tokens_used, chat_id, logprobs = self.llm.request_completion(self.prompt, max_tokens=300)
            # for gpt-4:
            #completion_text, tokens_used, chat_id, message_response = llm.request_chatcompletion(prompt, max_tokens = 300)
            #logprobs = None

            # tokens_used
            self.token_count += tokens_used

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
                    logging.warning('WARNING: completion_text not correct format! Skipping test sample')
                    logging.warning(completion_text)
                    completion_text = completion_text.split('\n')[0]
                # linkage word of test sample
                try:
                    linkage_predicted = completion_text.split('\n')[1].split(':')[1].strip()
                except:
                    logging.warning('WARNING: completion_text not correct format for linkage word!')
                    logging.warning(completion_text)
                    linkage_predicted = 'NA'

                # get reasoning
                try:
                    reasoning = completion_text.split('\n')[2].split(':')[1].strip()
                except:
                    logging.warning('WARNING: completion_text not correct format for reasoning!')
                    logging.warning(completion_text)
                    reasoning = 'NA'

                # probability of predicted class
                if logprobs is not None:
                    class_prob = logprobs[3]
                else:
                    class_prob = 0
            elif (len(completion_text.split('\n')) == 2) and completion_text.split('\n')[0].startswith('classification'):
                logging.warning('WARNING: completion_text has only 2 lines! Skipping reasoning')
                try:
                    class_predicted = completion_text.split('\n')[0].split(':')[1].strip()
                except:
                    logging.warning('WARNING: completion_text not correct format! Skipping test sample')
                    logging.warning(completion_text)
                    completion_text = completion_text.split('\n')[0]
                try:
                    linkage_predicted = completion_text.split('\n')[1].split(':')[1].strip()
                except:
                    logging.warning('WARNING: completion_text not correct format for linkage word!')
                    linkage_predicted = 'NA'
                reasoning = 'NA'
                if logprobs is not None:
                    class_prob = logprobs[3]
                else:
                    class_prob = 0
            else:
                logging.warning('WARNING: completion_text has not not enough lines!')
                logging.warning(completion_text)
                class_predicted = 'NA'
                linkage_predicted = 'NA'
                reasoning = 'NA'
                class_prob = 0

            class_prob = round(np.exp(class_prob),3)
            
            # add results to dataframe
            self.df_res.loc[index, 'predicted_classes'] = lct_string_to_int(class_predicted)
            self.df_res.loc[index, 'predicted_classes_name'] = class_predicted
            self.df_res.loc[index, 'confidence'] = class_prob
            self.df_res.loc[index, 'linkage_words'] = linkage_predicted
            self.df_res.loc[index, 'window_start'] = window_start
            self.df_res.loc[index, 'window_end'] = window_end
            self.df_res.loc[index, 'prompt_id'] = chat_id
            self.df_res.loc[index, 'filename_prompt'] = filename_prompt
            self.df_res.loc[index, 'filename_response'] = filename_response
            self.df_res.loc[index, 'tokens'] = tokens_used
            self.df_res.loc[index, 'modelname_llm'] = self.modelname_llm
            self.df_res.loc[index, 'reasoning'] = reasoning

            # save intermediate results to disk
            self.df_res.to_csv(self.fname_results, index=False)

            #print results
            logging.debug(f'Index: {index} | Prediction: {class_predicted} | Probability: {class_prob} | Used tokens: {tokens_used} ')
            logging.debug('')

        # Write token count to file
        filename_token_count = f'token_count_{self.modelname_llm}.txt'
        save_text(str(self.token_count), os.path.join(self.outpath, filename_token_count))

        logging.debug(f'Experiment finished! Results saved to folder {self.outpath}')

        return self.fname_results


def test_llmprocess():
    outpath = "../results_process/"

    # Path to schemas and excel files for definitions and examples:
    path_schema = "../schemas/"

    # Path to data files:
    path_data = "../tests"

    # Filename for sequencing definitions (.json or .xlsx), assumed to be in folder path_schema:
    filename_definitions = "sequencing_types.xlsx"

    # Filename for prompt instructions, assumed to be in folder path_schema:
    filename_zero_prompt = "instruction_prompt.txt"

    # Filename for clausing pairs, assumed to be in path data:
    filename_pairs = "sequences_test.csv"

    # Filename for text to be claused, assumed to be in path data:
    filename_text = "reference_text.txt"

    # Filename for examples (.json or .xlsx), assume to be in folder path_data:
    filename_examples = "sequencing_examples.xlsx"

    # OpenAI key file (do not share this file)
    filename_openai_key = "../../openai_key.txt"
    
    # run LLM process
    llm_process = LLMProcess(filename_pairs=os.path.join(path_data,filename_pairs),
                             filename_text=os.path.join(path_data, filename_text),
                             filename_examples=os.path.join(path_data, filename_examples),
                             filename_definitions=os.path.join(path_schema, filename_definitions),
                             filename_zero_prompt=os.path.join(path_schema, filename_zero_prompt),
                             outpath=outpath)
    
    #with open(filename_openai_key, 'r') as f:
    #    openai.api_key = f.read()
    #llm_process.run()
    
    llm_process.run(filename_openai_key)


if __name__ == "__main__":
    # get arguments from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--outpath', type=str, default="../results_llm/", help='The path to the output folder.', required=True)
    parser.add_argument('--filename_pairs', type=str, default="../tests/sequences_test.csv", help='The path+filename of the csv table with clausing pairs.', required=True)
    parser.add_argument('--filename_text', type=str, default="../tests/reference_text.txt", help='The path+filename of the text file with the text to be claused.', required=True)
    parser.add_argument('--filename_examples', type=str, default="../tests/sequencing_examples.xlsx", help='The path+filename of the examples json file.', required=False)
    parser.add_argument('--filename_definitions', type=str, default="../schemas/sequencing_types.xlsx", help='The path+filename of the definitions json file.', required=False)
    parser.add_argument('--filename_zero_prompt', type=str, default="../schemas/instruction_prompt.txt", help='The path+filename of the zero-shot instruction prompt text file.', required=False)
    parser.add_argument('--modelname_llm', type=str, default='gpt-3.5-turbo-instruct', help='The name of the LLM model to use.', required=False)
    args = parser.parse_args()

    # run experiment pipeline
    llm_process = LLMProcess(filename_pairs=args.filename_pairs,
                             filename_text=args.filename_text,
                            filename_examples=args.filename_examples,
                            filename_definitions=args.filename_definitions,
                            filename_zero_prompt=args.filename_zero_prompt,
                            outpath=args.outpath,
                            modelname_llm=args.modelname_llm)
    llm_process.run()
