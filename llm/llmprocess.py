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
import time
import math

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
    if not isinstance(text, str):
        text = str(text)
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
        logging.debug("No known classification exist for ", s)
        logging.debug("Need to be one of:", list(LCTclasses.__members__.keys()))
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
                 filename_zero_prompt="../schemas/instruction_multiprompt.txt",
                 outpath="../results_llm/",
                 modelname_llm="gpt-3.5-turbo-1106",
                 nseq_per_prompt = 8,
                 progress_update_fn=print):
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
        - nseq_per_prompt (int): The number of sequences per prompt.
        - progress_update_fn (Callable): The function to pass the process progress message to. Defaults to print

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
        self.nseq_per_prompt = nseq_per_prompt
        self.progress_update_fn = progress_update_fn

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
        self.df_res['corrected_classes'] = None
        self.df_res['linkage_words'] = None
        self.df_res['window_start'] =None
        self.df_res['window_end'] = None
        self.df_res['filename_prompt'] = None
        self.df_res['filename_response'] = None
        self.df_res['tokens'] = None
        self.df_res['modelname_llm'] = None
        self.df_res['reasoning'] = None

    def estimate_compute_cost(self, 
                              path_cost = './schemas/openai_pricing.json',
                              avg_token_instruction = 2500,
                              avg_token_sample = 250,
                              avg_token_output_per_seq = 450,
                              avg_time_per_seq = 2):
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
        nsamples = len(self.df_sequences)
        cost_schema = load_json(path_cost)
        ntokens_in = math.ceil(nsamples / self.nseq_per_prompt) * (avg_token_instruction + avg_token_sample * self.nseq_per_prompt) / 1000 
        ntokens_out= nsamples * avg_token_output_per_seq / 1000
        compute_time = nsamples * avg_time_per_seq 

        # check if modelname_llm is in cost_schema
        if self.modelname_llm not in cost_schema.keys():
            logging.warning('WARNING:', self.modelname_llm, 'not in cost_schema!')
            costs = None
        else:
            modelcost = cost_schema[self.modelname_llm]
            # check if modelcost includes "input" and "output"
            if 'input' in modelcost.keys() and 'output' in modelcost.keys():
                costs = modelcost['input'] * ntokens_in + modelcost['output'] * ntokens_out

            elif 'input_usage' in modelcost.keys() and 'output_usage' in modelcost.keys():
                costs = modelcost['input_usage'] * ntokens_in + modelcost['output_usage'] * ntokens_out
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
            example_string += f"""\nOutput\nReason: {row['Reasoning']}\n"""
            example_string += f"""Classification: {row['Sub_Subtype']}\n"""
            example_string += f"""Linkage word: {row['Linkage_Word']}\n"""
            example_string += f"""\n"""

        # replace example_types with example_types_short in example_string
        for example_type, example_type_short in zip(self.example_types, self.example_types_short):
            example_string = example_string.replace(example_type, example_type_short)

        self.zero_shot_prompt = self.zero_shot_prompt.replace('EXAMPLES', example_string)

        # add definitions to main_prompt
        self.zero_shot_prompt = self.zero_shot_prompt.replace('SEQUENCING_CLASSES', self.sequencing_classes)
        self.zero_shot_prompt = self.zero_shot_prompt.replace('DESCRIPTION_CLASSES', self.sequencing_definition)

    def gen_multiprompt(self, text_content_multi, text_chunk1_multi, text_chunk2_multi):
        # generate dict for each text in text_content_multi in format {text content: text_content, chunk 1: text_chunk_1, chunk 2: text_chunk_2}
        text_str = """"""
        id = range(0, len(text_content_multi))
        for i in id:
            text_str += str({'Sample ID': i, 'Text Content': text_content_multi[i], 'Clause 1': text_chunk1_multi[i], 'Clause 2': text_chunk2_multi[i]}) + '\n'
        return self.zero_shot_prompt.replace('TEXT_CONTENT', text_str)

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

        # split test samples in chunks of nseq_per_prompt
        list_text_chunk1 = []
        list_text_chunk2 = []
        list_text_content = []
        list_index = []
        list_window_start = []
        list_window_end = []
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
            list_text_chunk1.append(text_chunk_1)
            list_text_chunk2.append(text_chunk_2)
            list_text_content.append(text_content)
            list_index.append(index)
            list_window_start.append(window_start)
            list_window_end.append(window_end)
        list_text_content_multi = [list_text_content[i:i + self.nseq_per_prompt] for i in range(0, len(list_text_content), self.nseq_per_prompt)]
        list_text_chunk1_multi = [list_text_chunk1[i:i + self.nseq_per_prompt] for i in range(0, len(list_text_chunk1), self.nseq_per_prompt)]
        list_text_chunk2_multi = [list_text_chunk2[i:i + self.nseq_per_prompt] for i in range(0, len(list_text_chunk2), self.nseq_per_prompt)]
        list_index_multi = [list_index[i:i + self.nseq_per_prompt] for i in range(0, len(list_index), self.nseq_per_prompt)]
        list_window_start_multi = [list_window_start[i:i + self.nseq_per_prompt] for i in range(0, len(list_window_start), self.nseq_per_prompt)]
        list_window_end_multi = [list_window_end[i:i + self.nseq_per_prompt] for i in range(0, len(list_window_end), self.nseq_per_prompt)]

        # counts total number of sequences processed
        processed_seq_count: int = 0
        total_seq_count: int = self.df_sequences.shape[0]
        self.progress_update_fn(f"\r{processed_seq_count} of {total_seq_count} sequences complete", end="")
        for index_multi, text_content_multi, text_chunk1_multi, text_chunk2_multi, window_start_multi, window_end_multi in zip(list_index_multi, 
                                                                                         list_text_content_multi, 
                                                                                         list_text_chunk1_multi, 
                                                                                         list_text_chunk2_multi,
                                                                                         list_window_start_multi,
                                                                                         list_window_end_multi):

            
            nseq = len(index_multi)
            
            logging.debug('Processing clauses for samples', index_multi[0], ' to ', index_multi[-1])
           
            # copy string self.zero_shot_prompt
            self.prompt = self.gen_multiprompt(text_content_multi, 
                                               text_chunk1_multi, 
                                               text_chunk2_multi)


            # call OPenAi API with prompt
            completion_text, tokens_used, chat_id, logprobs = self.llm.request_chatcompletion(self.prompt, max_tokens=self.nseq_per_prompt * 300)

            # tokens_used
            self.token_count += tokens_used

            # add number of sequences processed for progress tracking
            processed_seq_count += self.nseq_per_prompt
            # account for fewer than self.nseq_per_prompt sequences
            processed_seq_count = min(processed_seq_count, total_seq_count)

            # save prompt to file
            filename_prompt = f'prompt_{chat_id}.txt'
            save_text(self.prompt, os.path.join(self.outpath_prompts, filename_prompt))

            if completion_text.startswith('\n'):
                completion_text = completion_text[1:]

            # check if response is json
            if completion_text.startswith('{') and completion_text.endswith('}'):     
                try:
                    completion_text = json.loads(completion_text)
                    # save response to json file
                    filename_response = f'response_{chat_id}.json'    
                    with open(os.path.join(self.outpath_prompts, filename_response), 'w') as f:
                        json.dump(completion_text, f, indent=2)  
                    # Extract classification, reasoning and linkage word from completion_text
                    keys = completion_text.keys()
                    list_reasoning = [completion_text[key]['reason'] for key in keys]
                    list_class_pred = [completion_text[key]['classification'] for key in keys]
                    list_linkage_pred = [completion_text[key]['linkage word'] for key in keys]
                except:
                    logging.warning('WARNING: completion_text not in correct format! Skipping test samples:', index_multi[0:-1])
                    filename_response = f'response_{chat_id}.txt' 
                    save_text(completion_text, os.path.join(self.outpath_prompts, filename_response))
                    logging.warning('LLM response text written to file:', os.path.join(self.outpath_prompts, filename_response))
                    list_reasoning = ['NONE'] * nseq
                    list_class_pred = ['NONE'] * nseq
                    list_linkage_pred = ['NONE'] * nseq
            else:
                logging.warning('WARNING: completion_text not in json format! Skipping test samples:', index_multi[0:-1])
                filename_response = f'response_{chat_id}.txt' 
                save_text(completion_text, os.path.join(self.outpath_prompts, filename_response))
                logging.warning('LLM response text written to file:', os.path.join(self.outpath_prompts, filename_response))
                list_reasoning = ['NONE'] * nseq
                list_class_pred = ['NONE'] * nseq
                list_linkage_pred = ['NONE'] * nseq

            
            # convert class_pred to int
            list_class_pred_int = [lct_string_to_int(class_pred) for class_pred in list_class_pred]
            # add results to dataframe
            self.df_res.loc[index_multi, 'predicted_classes'] = list_class_pred_int
            self.df_res.loc[index_multi, 'predicted_classes_name'] = list_class_pred
            self.df_res.loc[index_multi, 'corrected_classes'] = ["0"] * nseq
            self.df_res.loc[index_multi, 'linkage_words'] = list_linkage_pred
            self.df_res.loc[index_multi, 'window_start'] = window_start_multi
            self.df_res.loc[index_multi, 'window_end'] = window_end_multi
            self.df_res.loc[index_multi, 'filename_prompt'] = [filename_prompt] * nseq
            self.df_res.loc[index_multi, 'filename_response'] = [filename_response] * nseq
            self.df_res.loc[index_multi, 'tokens'] = [tokens_used/nseq] * nseq
            self.df_res.loc[index_multi, 'modelname_llm'] = [self.modelname_llm]* nseq
            self.df_res.loc[index_multi, 'reasoning'] = list_reasoning

            # save intermediate results to disk
            self.df_res.to_csv(self.fname_results, index=False)

            #print results
            logging.debug('Index:', index_multi, ' | Prediction:', list_class_pred, ' | Used tokens:', tokens_used)
            logging.debug('')

            # number of classes that are not 'NONE' or 'NA' in list_class_pred
            nclasses_found = len([class_pred for class_pred in list_class_pred if class_pred not in ['NONE', 'NA']])

            # print process message
            self.progress_update_fn(f"\r{processed_seq_count} of {total_seq_count} sequences complete", end="")

            # wait 3 seconds to avoid API call limit
            time.sleep(3)

        # Write token count to file
        filename_token_count = f'token_count_{self.modelname_llm}.txt'
        save_text(str(self.token_count), os.path.join(self.outpath, filename_token_count))

        logging.debug('Experiment finished! Results saved to folder', self.outpath)

        return self.fname_results
    
    def run_single(self, 
                   c1_start, 
                   c1_end, 
                   c2_start, 
                   c2_end, 
                   filename_prompt_single="../schemas/instruction_singleprompt.txt"):
        # Generate prompt for single pair
        window_start = c1_start
        window_end = c2_end
        text_chunk_1, text_chunk_2, text_content = self.get_text_chunks(self.filename_text, 
                                                                        c1_start, 
                                                                        c1_end,
                                                                        c2_start,
                                                                        c2_end,
                                                                        window_start,
                                                                        window_end)
        single_prompt = load_text(filename_prompt_single).format(text_content=text_content,
                                                                text_chunk_1=text_chunk_1,
                                                                text_chunk_2=text_chunk_2)
        #single_prompt = self.gen_singleprompt(text_content, text_chunk_1, text_chunk_2)

        # Call OpenAI API with the prompt
        completion_text, tokens_used, chat_id, _ = self.llm.request_chatcompletion(single_prompt, max_tokens=300)

        # Process the response
        if completion_text.startswith('\n'):
            completion_text = completion_text[1:]

        # Initialize the result dictionary
        result = {
            'predicted_class': None,
            'predicted_class_name': None,
            'linkage_words': None,
            'window_start': window_start,
            'window_end': window_end,
            'filename_prompt': None,
            'filename_response': None,
            'tokens': tokens_used,
            'reasoning': None
        }

        try:
            # Parse JSON response
            completion_json = json.loads(completion_text)
            result['predicted_class'] = completion_json.get('classification')
            result['predicted_class_name'] = lct_string_to_int(result['predicted_class'])
            result['linkage_words'] = completion_json.get('linkage word')
            result['reasoning'] = completion_json.get('reason')

            # Save the prompt and response
            filename_prompt = f'prompt_{chat_id}.txt'
            filename_response = f'response_{chat_id}.json'
            save_text(single_prompt, os.path.join(self.outpath, filename_prompt))
            with open(os.path.join(self.outpath, filename_response), 'w') as f:
                json.dump(completion_json, f, indent=2)

            result['filename_prompt'] = filename_prompt
            result['filename_response'] = filename_response

        except json.JSONDecodeError:
            # In case the response is not in JSON format
            result['reasoning'] = 'Response format error'

        return result



def test_llmprocess(debug = False):
    """
    Test function for LLMprocess.
    """
    # Set debug option to True for more verbose logging
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    # get time for compute time estimation
    start_time = time.time()

    outpath = "./results_process/"

    # Path to schemas and excel files for definitions and examples:
    path_schema = "./schemas/"

    # Path to data files:
    path_data = "./tests"

    # Filename for sequencing definitions (.json or .xlsx), assumed to be in folder path_schema:
    filename_definitions = "sequencing_types.xlsx"

    # Filename for prompt instructions, assumed to be in folder path_schema:
    filename_zero_prompt = "instruction_multiprompt.txt"

    # Filename for clausing pairs, assumed to be in path data:
    filename_pairs = "sequences_test.csv"

    # Filename for text to be claused, assumed to be in path data:
    filename_text = "reference_text.txt"

    # Filename for examples (.json or .xlsx), assume to be in folder path_data:
    filename_examples = "sequencing_examples.xlsx"

    # OpenAI key file (do not share this file)
    filename_openai_key = "../openai_key.txt"
    
    # run LLM process
    llm_process = LLMProcess(filename_pairs=os.path.join(path_data,filename_pairs),
                             filename_text=os.path.join(path_data, filename_text),
                             filename_examples=os.path.join(path_data, filename_examples),
                             filename_definitions=os.path.join(path_schema, filename_definitions),
                             filename_zero_prompt=os.path.join(path_schema, filename_zero_prompt),
                             outpath=outpath)
    
    # Estimate costs:
    compute_cost = llm_process.estimate_compute_cost()
    print(compute_cost)
    
    #with open(filename_openai_key, 'r') as f:
    #    openai.api_key = f.read()
    #llm_process.run()
    
    llm_process.run(filename_openai_key)

    # get time for compute time estimation and print in seconds
    compute_time = time.time() - start_time
    print(f'Compute time: {round(compute_time,1)} seconds')


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
