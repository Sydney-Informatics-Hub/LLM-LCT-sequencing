# Prompt experimenting for sequencing classification of text data

import os
import json
import random
import pandas as pd
import numpy as np
import json
import seaborn as sns
import matplotlib.pyplot as plt


from load_schema_json import load_json, validate_json, json_to_dataframe
#import importlib
#importlib.reload(utils_llm)
from utils_llm import LLM

# some paths and filenames
path_schema = "../schemas/"
filename_examples = "sequencing_examples_reason.json"
filename_schema = "schema_sequencing_examples_reason.json"
filename_definitions = "sequencing_types.json"
filename_zero_prompt = "instruction_prompt.txt"
outpath = "../results/"

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
    for example in selected_examples:
        example_list.append(example['Example'])
        reason_list.append(example['Reasoning'])
        linkage_list.append(example['Linkage_Word'])
    
    return example_list, reason_list, linkage_list


def example_train_test_split(df, Nsel=1, type_order='Sub_Subtype', random_seed=42):
    """
    Splits the example dataframe into training and testing sets, ensuring that each type has at least N examples in the training set.

    Parameters:
    -----------
    - df (pd.DataFrame): The input example dataframe.
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


def gen_prompt(zero_shot_prompt, sequencing_classes, description_classes, examples_classes, text_to_classify):
    zero_shot_prompt = zero_shot_prompt.replace('SEQUENCING_CLASSES', sequencing_classes)
    zero_shot_prompt = zero_shot_prompt.replace('DESCRIPTION_CLASSES', description_classes)
    zero_shot_prompt = zero_shot_prompt.replace('EXAMPLES_CLASSES', examples_classes)
    zero_shot_prompt = zero_shot_prompt.replace('TEXT_TO_CLASSIFY', text_to_classify)
    return zero_shot_prompt

def get_sequencing_classes():
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
    matrix = matrix.reindex(index=class_labels + [np.nan], columns=class_labels + [np.nan], fill_value=0)

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

    for metric, values in metrics.items():
        print(f"{metric}: {values}")

    if outfname is not None:
        with open(outfname, 'w') as file:
            json.dump(metrics, file, indent=2)

    return metrics



def eval_exp(df, outpath_exp):
    """
    generate confusion matrix from dataframe
    compare predicted labels (pred_class) with true labels (test_class)

    Parameters:
    -----------
    - df (pd.DataFrame): The dataframe with results from the experiment, including:
        - pred_class (str): The predicted class.
        - test_class (str): The true class.
    """
    seq_classes = get_sequencing_classes()
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



def exp_pipe():
    """
    This pipe function is used to generate the prompts for the experiment.
    """
    # initialize token_counter
    token_count = 0
    modelname_llm = 'gpt-3.5-turbo-instruct'

    examples = load_json(os.path.join(path_schema, filename_examples))
    schema = load_json(os.path.join(path_schema, filename_schema))
    assert validate_json(examples, schema), "JSON data is invalid!"
    df = json_to_dataframe(examples)

    # Select examples for each type
    example_types = df['Sub_Subtype'].unique()

    # get first three letter characters of example types and write in captial letters
    example_types_short = [example_type[:3].upper() for example_type in example_types]

    # split in train and test samples
    train_df, test_df = example_train_test_split(df, Nsel=1)
    # loop over train_df and add to example string
    example_string = """ """
    for index, row in train_df.iterrows():
        example_string += f"""example: {row['Example']}\n"""
        example_string += f"""classification: {row['Sub_Subtype']}\n"""
        example_string += f"""linkage word: {row['Linkage_Word']}\n"""
        example_string += f"""\n"""

    # replace example_types with example_types_short in example_string
    for example_type, example_type_short in zip(example_types, example_types_short):
        example_string = example_string.replace(example_type, example_type_short)

    list_test_str = []
    list_test_class = []
    list_test_linkage = []
    for index, row in test_df.iterrows():
        list_test_str.append(row['Example'])
        list_test_class.append(row['Sub_Subtype'])
        list_test_linkage.append(row['Linkage_Word'])

    # load definitions from json file
    sequencing_classes = get_sequencing_classes()
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
        list_exp_folders.sort()
        last_exp_folder = list_exp_folders[-1]
        last_exp_folder_number = int(last_exp_folder[3:])
        outpath_exp = os.path.join(outpath, f'exp{last_exp_folder_number+1}')
    os.makedirs(outpath_exp, exist_ok=True)

    # initiate results dataframe
    df_results = pd.DataFrame(columns=[
        'test_str', 
        'test_class', 
        'test_linkage', 
        'pred_class', 
        'pred_class_prob',  
        'pred_linkage', 
        'prompt_id', 
        'filename_prompt', 
        'filename_response', 
        'tokens', 
        'modelname_llm', 
        'reasoning'])

    # Loop over test sample in list_test_str
    n_test = 0
    for test_str, test_class, test_linkage in zip(list_test_str, list_test_class, list_test_linkage):
        print(f"Test sample {n_test} of {len(list_test_str)}")
        # generate prompt
        prompt = gen_prompt(zero_shot_prompt, sequencing_classes, sequencing_definition, example_string, test_str)

        # replace in prompt all occurences of example_types with f'{example_type} (example_type_short)'
        for example_type, example_type_short in zip(example_types, example_types_short):
            prompt = prompt.replace(example_type, f'{example_type} ({example_type_short})')

        # call OPenAi API with prompt
        llm = LLM(filename_openai_key='../../openai_key.txt', model_name = modelname_llm)
        completion_text, tokens_used, chat_id, logprobs = llm.request_completion(prompt, max_tokens = 300)
        # for gpt-4:
        #completion_text, tokens_used, chat_id, message_response = llm.request_chatcompletion(prompt, max_tokens = 300)
        #logprobs = None

         # tokens_used
        token_count += tokens_used

        # save prompt to file
        filename_prompt = f'prompt_{chat_id}.txt'
        save_text(prompt, os.path.join(outpath_exp, filename_prompt))

        # save response to file
        filename_response = f'response_{chat_id}.txt'
        save_text(completion_text, os.path.join(outpath_exp, filename_response))

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
            # lingage word of test sample
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

        #print results
        print(f'Tested class: {test_class}')
        print(f'Predicted class: {class_predicted}')
        print(f'Predicted class probability: {class_prob}')
        print(f'Used tokens: {token_count}')

        #add a new row to df_results
        row = [
            test_str, 
            test_class, 
            test_linkage, 
            class_predicted, 
            class_prob, 
            linkage_predicted, 
            chat_id, 
            filename_prompt, 
            filename_response, 
            tokens_used, 
            modelname_llm, 
            reasoning]
        df_results.loc[len(df_results)] = row

        # increase n_test
        n_test += 1

    # convert class_prob from log to prob
    df_results['pred_class_prob'] = df_results['pred_class_prob'].apply(lambda x: np.exp(x))

    # save results to csv file
    filename_results = f'results_{modelname_llm}.csv'
    df_results.to_csv(os.path.join(outpath_exp, filename_results), index=False)
    # Write token count to file
    filename_token_count = f'token_count_{modelname_llm}.txt'
    save_text(str(token_count), os.path.join(outpath_exp, filename_token_count))

    # evaluate results and save to fiile
    eval_exp(df_results, outpath_exp)
