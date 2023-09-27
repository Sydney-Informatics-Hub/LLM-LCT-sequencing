# Prompt experimenting for sequencing classification of text data

"""
ToDo:
- add tokenizer counter
- add API calls
- add evaluation

"""
import os
import json
import random
import pandas as pd

from load_schema_json import load_json, validate_json, json_to_dataframe
from utils_llm import LLM

# some paths and filenames
path_schema = "../schemas/"
filename_examples = "sequencing_examples_reason.json"
filename_schema = "schema_sequencing_examples_reason.json"
filename_definitions = "sequencing_types_clean.json"
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


def exp_pipe():
    """
    This pipe function is used to generate the prompts for the experiment.
    """
    # initialize token_counter
    token_count = 0
    modelname_llm = 'gpt-3.5-turbo'

    examples = load_json(os.path.join(path_schema, filename_examples))
    schema = load_json(os.path.join(path_schema, filename_schema))
    assert validate_json(examples, schema), "JSON data is invalid!"
    df = json_to_dataframe(examples)

    # Select examples for each type
    example_types = df['Sub_Subtype'].unique()

    # split in train and test samples
    train_df, test_df = example_train_test_split(df, Nsel=1)
    # loop over train_df and add to example string
    example_string = """ """
    for index, row in train_df.iterrows():
        example_string += f"""example: {row['Example']}\n"""
        example_string += f"""classification: {row['Sub_Subtype']}\n"""
        example_string += f"""linkage word: {row['Linkage_Word']}\n"""
        example_string += f"""\n"""

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

    os.makedirs(outpath, exist_ok=True)

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
    for test_str, test_class, test_linkage in zip(list_test_str, list_test_class, list_test_linkage):
        # generate prompt
        prompt = gen_prompt(zero_shot_prompt, sequencing_classes, sequencing_definition, example_string, test_str)

        # call OPenAi API with prompt
        llm = LLM(filename_openai_key='../../openai_key.txt', model_name = modelname_llm)
        completion_text, tokens_used, chat_id, logprobs = llm.request_completion(prompt, max_tokens = 300)

         # tokens_used
        token_count += tokens_used

        # save prompt to file
        filename_prompt = f'prompt_{chat_id}.txt'
        save_text(prompt, os.path.join(outpath, filename_prompt))

        # save response to file
        filename_response = f'response_{chat_id}.txt'
        save_text(completion_text, os.path.join(outpath, filename_response))

        # class of test sample
        class_predicted = completion_text.split('\n')[1].split(':')[1].strip()

        # lingage word of test sample
        linkage_predicted = completion_text.split('\n')[2].split(':')[1].strip()

        # get reasoning
        reasoning = completion_text.split('\n')[3].split(':')[1].strip()

        # probability of predicted class
        class_prob = logprobs[3]

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

    # save results to csv file
    filename_results = f'results_{modelname_llm}.csv'
    df_results.to_csv(os.path.join(outpath, filename_results), index=False)



