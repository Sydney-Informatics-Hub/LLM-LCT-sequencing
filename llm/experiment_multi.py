""" Main module for prompt experimenting for sequencing classification of text data

This module contains the main functions for running the experiment pipeline for the sequencing classification of text data.

Example:
    Clone the repo and run the following command from the command line:
        $ python experiment.py --outpath ../results/
    
    To run the experiment with different parameters, use the following command:
        $ python experiment.py --outpath ../results/ 
                            --path_schema ../schemas 
                            --filename_examples sequencing_examples_reason.json 
                            --filename_schema schema_sequencing_examples_reason.json 
                            --filename_definitions sequencing_types.json 
                            --filename_zero_prompt instruction_prompt.txt 
                            --modelname_llm gpt-3.5-turbo-instruct 
                            --list_prompt_indices 0 1 2 3 4 5 6 7
"""

import os
import random
import pandas as pd
import numpy as np
import json
import argparse
import seaborn as sns
import matplotlib.pyplot as plt
import time


from .load_schema_json import load_json, validate_json, json_to_dataframe
from .excel_json_converter import excel_to_json
#import importlib
#importlib.reload(utils_llm)
from .utils_llm import LLM

#from llm.load_schema_json import load_json, validate_json, json_to_dataframe
#from llm.excel_json_converter import excel_to_json
#from llm.utils_llm import LLM

"""
# some paths and filenames
path_schema = "../schemas/"
filename_examples = "sequencing_examples_reason.json"
filename_schema = "schema_sequencing_examples_reason.json"
filename_definitions = "sequencing_types.json"
filename_zero_prompt = "instruction_prompt.txt"
outpath = "../results/"

# LLM modelname
modelname_llm = 'gpt-3.5-turbo-instruct'
"""

# 
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


def select_examples_by_type(examples, example_type, n_examples, type_order = 'Sub_Subtype', random_seed=42):
    """
    Selects a specified number of examples randomly based on the given type.

    Parameters:
    -----------
    - examples (dict): The examples data.
    - example_type (str): The type of example to select.
    - n_examples (int): The number of examples to select.
    - type_order (str): The order of the types to select from ('Type', 'Subtype', 'Sub_Subtype'). 
        Default is 'Sub_Subtype'.
    - random_seed (int): The random seed to use for reproducibility. Default is 42.

    Returns:
    --------
    - example list: A list of randomly selected examples of the specified type.
    - reason list: A list of the reasons for the selected examples.
    - linkage list: A list of the linkage words for the selected examples.
    """

    # Filter examples by the given type
    filtered_examples = [example for example in examples['Data'] if example[type_order] == example_type]
    
    # Extract the 'Examples' from each filtered example and flatten the list
    all_examples = [item for sublist in [ex['Examples'] for ex in filtered_examples] for item in sublist]
    
    # Randomly select the specified number of examples
    random.seed(random_seed)
    selected_examples = random.sample(all_examples, min(n_examples, len(all_examples)))

    # return the selected examples, reasons, and linkage words
    example_list = []
    reason_list = []
    linkage_list = []
    #clause1_list = []
    #clause2_list = []
    for example in selected_examples:
        example_list.append(example['Example'])
        reason_list.append(example['Reasoning'])
        linkage_list.append(example['Linkage_Word'])
        # check if example contains two clauses
    
    return example_list, reason_list, linkage_list


def example_train_test_split(df, list_prompt_indices=None, Nsel=1, type_order='Sub_Subtype', random_seed=42):
    """
    Splits the example dataframe into training and testing sets, ensuring that each type has at least N examples in the training set.

    Parameters:
    -----------
    - df (pd.DataFrame): The input example dataframe.
    - list_prompt_indices (list): A list of indices of examples to use in the prompt instruction. If None, the prompt/ test set will be randomly selected.
    - Nsel (int): The minimum number of examples for each type in the training set.
    - type_order (str): The order of the types to select from ('Type', 'Subtype', 'Sub_Subtype').
        Default is 'Sub_Subtype'.
    - random_seed (int): The random seed to use for reproducibility. Default is 42.

    Returns:
    --------
    - train_df (pd.DataFrame): The training set.
    - test_df (pd.DataFrame): The testing set.
    """
    
    train_data = []
    test_data = []

    if (list_prompt_indices is not None) and (len(list_prompt_indices) > 0):
        # Split the dataframe into training and testing sets based on the given indices
        train_df = df.iloc[list_prompt_indices]
        test_df = df.drop(list_prompt_indices)
        # reindex the dataframes
        train_df = train_df.reset_index(drop=True)
        test_df = test_df.reset_index(drop=True)
        return train_df, test_df

    else:
        for type_, group in df.groupby(type_order):
            if len(group) <= Nsel:
                train_data.append(group)
            else:
                train_data.append(group.sample(n=Nsel, random_state=random_seed))
                test_data.append(group.drop(train_data[-1].index))

        train_df = pd.concat(train_data).reset_index(drop=True)
        test_df = pd.concat(test_data).reset_index(drop=True)

        return train_df, test_df


def merge_definitions_examples(definitions, example_subset, linkage_subset):
    """
    Merge the class definitions with the example subset and linkage subset.

    Parameters:
    -----------
    - definitions (dict): The cdefinitions for the prompt.
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


def test_select_examples_by_type():
    examples = load_json(os.path.join(path_schema, filename_examples))
    schema = load_json(os.path.join(path_schema, filename_schema))
    assert validate_json(examples, schema), "JSON data is invalid!"
    example_type = 'Consequential Sequencing'
    nsel = 2
    examples_sel, reasons_sel, linkages_sel = select_examples_by_type(examples, example_type, nsel)
    assert len(examples_sel) == nsel
    assert len(reasons_sel) == nsel
    assert len(linkages_sel) == nsel


def gen_multiprompt(zero_shot_prompt, sequencing_classes, description_classes, examples_classes, text_content, text_chunk_1, text_chunk_2):
    zero_shot_prompt = zero_shot_prompt.replace('SEQUENCING_CLASSES', sequencing_classes)
    zero_shot_prompt = zero_shot_prompt.replace('DESCRIPTION_CLASSES', description_classes)
    zero_shot_prompt = zero_shot_prompt.replace('EXAMPLES_CLASSES', examples_classes)

    # generate dict for each text uin text_content, text_chunk_1, text_chunk_2queries in format {text content: text_content, chunk 1: text_chunk_1, chunk 2: text_chunk_2}
    text_str = """"""
    id = range(0, len(text_content))
    for i in id:
        text_str += str({'Sample ID': i, 'Text Content': text_content[i], 'Clause 1': text_chunk_1[i], 'Clause 2': text_chunk_2[i]}) + '\n'
  
    #text_dict = {'text content': text_content, 'Clause 1': text_chunk_1, 'Clause 2': text_chunk_2}
    zero_shot_prompt = zero_shot_prompt.replace('TEXT_CONTENT', text_str)
    return zero_shot_prompt

def gen_prompt(zero_shot_prompt, sequencing_classes, description_classes, examples_classes, text_content, text_chunk_1, text_chunk_2):
    # Generate prompt for multiple sequencing classes
    zero_shot_prompt = zero_shot_prompt.replace('SEQUENCING_CLASSES', sequencing_classes)
    zero_shot_prompt = zero_shot_prompt.replace('DESCRIPTION_CLASSES', description_classes)
    zero_shot_prompt = zero_shot_prompt.replace('EXAMPLES_CLASSES', examples_classes)
    zero_shot_prompt = zero_shot_prompt.replace('TEXT_CONTENT', text_content)
    zero_shot_prompt = zero_shot_prompt.replace('CHUNK_1', text_chunk_1)
    zero_shot_prompt = zero_shot_prompt.replace('CHUNK_2', text_chunk_2)
    return zero_shot_prompt

def get_sequencing_classes(path_schema, filename_definitions):
    definitions = load_json(os.path.join(path_schema, filename_definitions))
    # find all sub_subtypes in definitions
    sub_subtypes = []
    for definition in definitions['Sequencing_Types']:
        for subtype in definition['Subtypes']:
            for subsubtype in subtype['Sub_Subtypes']:
                # add subsubtype to list if not already in list
                if subsubtype['Sub_Subtype'] not in sub_subtypes:
                    sub_subtypes.append(subsubtype['Sub_Subtype'])
    return sub_subtypes


def gen_confusion_matrix(classes_test, classes_pred, class_labels, outfname_plot, plot_show = True):
    """
    generate confusion matrix and plots it.

    Parameters
    ----------
    classes_test: list of true classes
    classes_pred: list of predicted classes
    class_labels: list of all class labels
    outfname_plot: path + filename for output plot
    plot_show: if True show plot

    Return
    ----------
    array: 2D confusion matrix
    """

    matrix = pd.crosstab(pd.Series(classes_test, name='Actual'),
                         pd.Series(classes_pred, name='Predicted'),
                         dropna=False)
    
    # Reindex the matrix to ensure all classes are present
    #matrix = matrix.reindex(index=class_labels + [np.nan], columns=class_labels + [np.nan], fill_value=0)
    matrix = matrix.reindex(index=class_labels + ['NA'], columns=class_labels + ['NA'], fill_value=0)

    # plot matrix
    plt.figure(figsize=(10, 7))
    sns.heatmap(matrix, annot=True, cmap='Blues', fmt='g')
    plt.savefig(outfname_plot, dpi=300)
    if plot_show:
        plt.show()
    return matrix


def metrics_from_confusion_matrix(confusion_matrix, outfname=None):
    """
    Calculate accuracy, recall, and precision from a confusion matrix.
    
    Parameters:
    - confusion_matrix: DataFrame representing the confusion matrix
    - outfname: json filename to save metrics. If None provided, metrics will not be saved
    
    Returns:
    - accuracy, recall, precision dictionaries for each class and their macro-averages
    """
    
    # Removing the 'nan' columns and rows for metric calculations
    matrix_no_nan = confusion_matrix.drop(index=np.nan, columns=np.nan, errors='ignore')

    # True Positives (diagonal of the confusion matrix)
    TP = matrix_no_nan.values.diagonal()

    # False Positives (sum of columns minus TP)
    FP = matrix_no_nan.sum(axis=0) - TP

    # False Negatives (sum of rows minus TP)
    FN = matrix_no_nan.sum(axis=1) - TP

    # True Negatives (total samples minus TP + FP + FN)
    total_samples = matrix_no_nan.sum(axis=1)#.sum()
    TN = FN * 0
    #TN = total_samples - TP - FP - FN
    # for single-class classification, TN is always 0

    # Calculating metrics for each class
    accuracy = ((TP + TN)  / total_samples).to_dict()
    recall = (TP / (TP + FN)).to_dict()
    precision = (TP / (TP + FP)).to_dict()

    # Calculating mean-averages 
    macro_accuracy = np.round(np.nanmean(np.array(list(accuracy.values()))),4)
    macro_recall =  np.round(np.nanmean(np.array(list(recall.values()))),4)
    macro_precision = np.round(np.nanmean(np.array(list(precision.values()))),4)

    metrics = {
        'accuracy': accuracy,
        'recall': recall,
        'precision': precision,
        'mean_accuracy': macro_accuracy,
        'mean_recall': macro_recall,
        'mean_precision': macro_precision
    }

    print("------ Experiment Results ------")
    for metric, values in metrics.items():
        print(f"{metric}: {values}")
    print("--------------------------------")

    if outfname is not None:
        with open(outfname, 'w') as file:
            json.dump(metrics, file, indent=2)

    return metrics



def eval_exp(df, outpath_exp, seq_classes):
    """
    generate confusion matrix from dataframe
    compare predicted labels (pred_class) with true labels (test_class)

    Parameters:
    -----------
    - df (pd.DataFrame): The dataframe with results from the experiment, including:
        - pred_class (str): The predicted class.
        - test_class (str): The true class.
    """
    if len(seq_classes[0])>3:
        seq_classes = [seq_class[:3].upper() for seq_class in seq_classes]
    classes_test = df['test_class'].values
    if len(classes_test[0])>3:
        classes_test = [class_[:3].upper() for class_ in classes_test]
    classes_pred = df['pred_class'].values
    if len(classes_pred[0])>3:
        classes_pred = [class_[:3].upper() for class_ in classes_pred]

    outfname_plot = os.path.join(outpath_exp, 'confusion_matrix.png')
    confusion_matrix = gen_confusion_matrix(classes_test, classes_pred, seq_classes, outfname_plot)
    # calculate accuracy
    metrics = metrics_from_confusion_matrix(confusion_matrix, outfname = os.path.join(outpath_exp, 'metrics.json'))



def run_pipe(
        outpath = "../results/", 
        path_schema = '../schemas', 
        filename_examples = "sequencing_examples_2clauses_converted.json", 
        filename_schema = "schema_sequencing_examples_reason.json", 
        filename_definitions = "sequencing_types.json", 
        filename_zero_prompt = "instruction_multiprompt.txt", 
        modelname_llm = 'gpt-3.5-turbo-1106',
        list_prompt_indices = None,
        nseq_per_prompt = 4
        ):
    """
    This experiment pipeline includes the following main steps:
    - load examples from json file
    - split examples in train and test samples
    - generate prompt string
    - call OpenAI API
    - save prompt and response to file
    - save results to csv file

    Parameters:
    -----------
    - outpath (str): The path to the output folder.
    - path_schema (str): The path to the schema folder.
    - filename_examples (str): The filename of the examples json file.
    - filename_schema (str): The filename of the schema json file.
    - filename_definitions (str): The filename of the definitions json file.
    - filename_zero_prompt (str): The filename of the zero-shot instruction prompt text file.
    - modelname_llm (str): The name of the LLM model to use.
    - list_prompt_indices (list): A list of indices of examples to use in the prompt instruction. If None, the prompt/ test set will be randomly selected.
    - nseq_per_prompt (int): The number of sequence pairs to run in one prompt. 

    Returns:
    --------
    - df_results (pd.DataFrame): The dataframe with results from the experiment, including:
        - test_str (str): The test sample.
        - test_chunk1 (str): The first clause of the test sample.
        - test_chunk2 (str): The second clause of the test sample.
        - test_class (str): The true class.
        - test_linkage (str): The true linkage word.
        - pred_class (str): The predicted class.
        - pred_class_prob (float): The probability of the predicted class.
        - pred_linkage (str): The predicted linkage word.
        - prompt_id (str): The prompt id.
        - filename_prompt (str): The filename of the prompt text file.
        - filename_response (str): The filename of the response text file.
        - tokens (int): The number of tokens used.
        - modelname_llm (str): The name of the LLM model used.
        - reasoning (str): The reasoning for the predicted class.
    - outpath_exp (str): The path to the output folder for this experiment.
    - seq_classes (list): The list of sequencing classes.

    """
    # Check if filename_examples is excel file
    if filename_examples.endswith(".xlsx"):
        # convert filename_examples to json
        json_filename_out = filename_examples.replace(".xlsx", "_converted.json")
        excel_to_json(os.path.join(path_schema, filename_examples), 
                    os.path.join(path_schema, json_filename_out))
        filename_examples = json_filename_out

    # Check if filename_definitions is excel file
    if filename_definitions.endswith(".xlsx"):
        # convert filename_definitions to json
        json_filename_out = filename_definitions.replace(".xlsx", "_converted.json")
        excel_to_json(os.path.join(path_schema, filename_definitions), 
                    os.path.join(path_schema, json_filename_out))
        filename_definitions = json_filename_out

    # initialize token_counter
    token_count = 0

    examples = load_json(os.path.join(path_schema, filename_examples))
    schema = load_json(os.path.join(path_schema, filename_schema))
    assert validate_json(examples, schema)
    df = json_to_dataframe(examples)

    # Select examples for each type
    example_types = df['Sub_Subtype'].unique()

    # get first three letter characters of example types and write in captial letters
    example_types_short = [example_type[:3].upper() for example_type in example_types]

    # split in train and test samples
    train_df, test_df = example_train_test_split(df, list_prompt_indices=list_prompt_indices, Nsel=1)
    # loop over train_df and add to example string

    example_string = """ """
    for index, row in train_df.iterrows():
        clause1 = row['Linked_Chunk_1']
        clause2 = row['Linked_Chunk_2']
        text = row['Example']
        # f
        example_string += f"""Input\nText content: {row['Example']}\n"""
        example_string += f"""Clause 1: {row['Linked_Chunk_1']}\n"""
        example_string += f"""Clause 2: {row['Linked_Chunk_2']}\n"""
        example_string += f"""Reason: {row['Reasoning']}\n"""
        example_string += f"""\nAnswer\nClassification: {row['Sub_Subtype']}\n"""
        example_string += f"""Linkage word: {row['Linkage_Word']}\n"""
        example_string += f"""\n"""

    # replace example_types with example_types_short in example_string
    for example_type, example_type_short in zip(example_types, example_types_short):
        example_string = example_string.replace(example_type, example_type_short)

    list_test_str = []
    list_test_chunk1 = []
    list_test_chunk2 = []
    list_test_class = []
    list_test_linkage = []
    for index, row in test_df.iterrows():
        list_test_str.append(row['Example'])
        list_test_chunk1.append(row['Linked_Chunk_1'])
        list_test_chunk2.append(row['Linked_Chunk_2'])
        list_test_class.append(row['Sub_Subtype'])
        list_test_linkage.append(row['Linkage_Word'])

    # load definitions from json file
    sequencing_classes = get_sequencing_classes(path_schema, filename_definitions)

    # add also a three letter characters and write in captial letters
    seq_classes = [seq_class[:3].upper() for seq_class in sequencing_classes]

    # convert list to string
    sequencing_classes = ', '.join(f"'{item}'" for item in sequencing_classes)

    sequencing_dict = load_json(os.path.join(path_schema, filename_definitions))
    
    # convert dict to string
    sequencing_definition = json.dumps(sequencing_dict, indent=2)

    # load prompt string from instruction text file
    zero_shot_prompt= load_text(os.path.join(path_schema, filename_zero_prompt))

    # generate outpath
    os.makedirs(outpath, exist_ok=True)
    # check if outpath includes a folder that starts with string 'exp'
    # if so, add 1 to the number of the folder
    # if not, create folder 'exp1'
    list_folders = os.listdir(outpath)
    list_exp_folders = [folder for folder in list_folders if folder.startswith('exp')]
    if len(list_exp_folders) == 0:
        outpath_exp = os.path.join(outpath, 'exp1')
    else:
        exp_folder_numbers = [int(folder[3:]) for folder in list_exp_folders]
        exp_folder_numbers.sort()
        last_exp_folder_number = exp_folder_numbers[-1]
        outpath_exp = os.path.join(outpath, f'exp{last_exp_folder_number+1}')
    os.makedirs(outpath_exp, exist_ok=True)

    # initiate results dataframe
    df_results = pd.DataFrame(columns=[
        'test_str', 
        'test_chunk1',
        'test_chunk2',
        'test_class', 
        'test_linkage', 
        'pred_class',  
        'pred_linkage', 
        'filename_prompt', 
        'filename_response', 
        'tokens', 
        'modelname_llm', 
        'reasoning'])

    # Initiate LLM with API key
    llm = LLM(filename_openai_key=None, model_name = modelname_llm)

    # split test samples in chunks of nseq_per_prompt
    list_test_str_multi = [list_test_str[i:i + nseq_per_prompt] for i in range(0, len(list_test_str), nseq_per_prompt)]
    list_test_chunk1_multi = [list_test_chunk1[i:i + nseq_per_prompt] for i in range(0, len(list_test_chunk1), nseq_per_prompt)]
    list_test_chunk2_multi = [list_test_chunk2[i:i + nseq_per_prompt] for i in range(0, len(list_test_chunk2), nseq_per_prompt)]
    list_test_class_multi = [list_test_class[i:i + nseq_per_prompt] for i in range(0, len(list_test_class), nseq_per_prompt)]
    list_test_linkage_multi = [list_test_linkage[i:i + nseq_per_prompt] for i in range(0, len(list_test_linkage), nseq_per_prompt)]

    # Loop over test sample in list_test_class_multi
    n_test = 0
    for test_str, test_chunk1, test_chunk2, test_class, test_linkage in zip(list_test_str_multi, list_test_chunk1_multi, list_test_chunk2_multi, list_test_class_multi, list_test_linkage_multi):
        if n_test+nseq_per_prompt <= len(list_test_str):
            nseq = nseq_per_prompt
        else:
            nseq = len(list_test_str) - n_test
        print(f"Processing samples {n_test} to {n_test+nseq} of {len(list_test_str)}...")
        # generate prompt 
        prompt = gen_multiprompt(zero_shot_prompt, sequencing_classes, sequencing_definition, example_string, test_str, test_chunk1, test_chunk2)

        # replace in prompt all occurences of example_types with f'{example_type} (example_type_short)'
        for example_type, example_type_short in zip(example_types, example_types_short):
            prompt = prompt.replace(example_type, f'{example_type} ({example_type_short})')

        # call OPenAi API with prompt
        completion_text, tokens_used, chat_id, logprobs = llm.request_chatcompletion(prompt, max_tokens = nseq_per_prompt * 300)
        # for gpt-4:
        #completion_text, tokens_used, chat_id, message_response = llm.request_chatcompletion(prompt, max_tokens = 300)
        #logprobs = None

         # tokens_used
        token_count += tokens_used

        # save prompt to file
        filename_prompt = f'prompt_{chat_id}.txt'
        save_text(prompt, os.path.join(outpath_exp, filename_prompt))

        if completion_text.startswith('\n'):
            completion_text = completion_text[1:]

        # check if response is json
        if completion_text.startswith('{') and completion_text.endswith('}'): 
            # save response to json file
            completion_text = json.loads(completion_text)
            filename_response = f'response_{chat_id}.json'    
            with open(os.path.join(outpath_exp, filename_response), 'w') as f:
                json.dump(completion_text, f, indent=2)         
            try:
                #completion_text = json.loads(completion_text)
                #completion_text = load_json(os.path.join(outpath_exp, filename_response))
                keys = completion_text.keys()
                list_reasoning = [completion_text[key]['reason'] for key in keys]
                list_class_pred = [completion_text[key]['classification'] for key in keys]
                list_linkage_pred = [completion_text[key]['linkage word'] for key in keys]
            except:
                print('WARNING: completion_text not correct format! Skipping test samples')
                print(completion_text)
                list_reasoning = ['NA'] * nseq
                list_class_pred = ['NA'] * nseq
                list_linkage_pred = ['NA'] * nseq
        else:
            print('WARNING: completion_text not in json format! Skipping test samples')
            filename_response = f'response_{chat_id}.txt' 
            save_text(completion_text, os.path.join(outpath_exp, filename_response))

        # load json file

        #add a new row to df_results
        lst_nseq = [
            test_str, 
            test_chunk1,
            test_chunk2,
            test_class, 
            test_linkage, 
            list_class_pred, 
            list_linkage_pred, 
            [filename_prompt] * nseq, 
            [filename_response] * nseq, 
            [tokens_used/nseq] * nseq,
            [modelname_llm]* nseq, 
            list_reasoning
        ]
        transposed_list = [list(column) for column in zip(*lst_nseq)]
        for i, col in enumerate(transposed_list):
            df_results.loc[len(df_results)] = col

        # increase n_test
        n_test += nseq

        # wait 1 seq to not exceed API limit
        time.sleep(3)

    # save results to csv file
    filename_results = f'results_{modelname_llm}.csv'
    df_results.to_csv(os.path.join(outpath_exp, filename_results), index=False)
    # Write token count to file
    filename_token_count = f'token_count_{modelname_llm}.txt'
    save_text(str(token_count), os.path.join(outpath_exp, filename_token_count))

    print(f'Experiment finished! Results saved to folder {outpath_exp}')

    return df_results, outpath_exp, seq_classes


def test_pipe():
    # run experiment pipeline
    df_results, outpath_exp, seq_classes = run_pipe()

    # evaluate results and save to file
    eval_exp(df_results, outpath_exp, seq_classes)

if __name__ == "__main__":
    # get arguments from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--outpath', type=str, default="../results/", help='The path to the output folder.', required=False)
    parser.add_argument('--path_schema', type=str, default='../schemas', help='The path to the schema folder.', required=False)
    parser.add_argument('--filename_examples', type=str, default="sequencing_examples_reason.json", help='The filename of the examples json file.', required=False)
    parser.add_argument('--filename_schema', type=str, default="schema_sequencing_examples_reason.json", help='The filename of the schema json file.', required=False)
    parser.add_argument('--filename_definitions', type=str, default="sequencing_types.json", help='The filename of the definitions json file.', required=False)
    parser.add_argument('--filename_zero_prompt', type=str, default="instruction_prompt.txt", help='The filename of the zero-shot instruction prompt text file.', required=False)
    parser.add_argument('--modelname_llm', type=str, default='gpt-3.5-turbo-instruct', help='The name of the LLM model to use.', required=False)
    parser.add_argument('--list_prompt_indices', type=str, nargs='+', default=None, help='A list of indices of examples to use in the prompt instruction. If None, the prompt/test set will be randomly selected.', required=False)
    args = parser.parse_args()

    # run experiment pipeline
    df_results, outpath_exp, seq_classes = run_pipe(
        outpath = args.outpath, 
        path_schema = args.path_schema, 
        filename_examples = args.filename_examples, 
        filename_schema = args.filename_schema, 
        filename_definitions = args.filename_definitions, 
        filename_zero_prompt = args.filename_zero_prompt, 
        modelname_llm = args.modelname_llm,
        list_prompt_indices = args.list_prompt_indices)
    
    
    # evaluate results and save to file
    eval_exp(df_results, outpath_exp, seq_classes)
