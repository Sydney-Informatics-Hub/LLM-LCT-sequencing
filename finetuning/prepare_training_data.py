""" Script for preparing the training data for OpenAI finetuning

The script loads the training data, cleans it, splits it into train and validation sets, 
and converts it into the format required for OpenAI finetuning.

The system prompt and query template are defined in step 3. The system prompt is the same for all examples,
Note that the system prompt has to be the same as the one used for applying the finetuned model in the application later.
"""

import pandas as pd
import numpy as np
import json
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import tiktoken
from collections import defaultdict

# File path settings
file_path = '../../data/trainingdata.xlsx'
outpath_train = '../../data/data_openai_train.jsonl'
outpath_val = '../../data/data_openai_val.jsonl'


### 1. Data loading and cleaning

data = pd.read_excel(file_path)

# Convert all values in the 'Types' column to lowercase
data['Types'] = data['Types'].str.lower()
# remove leading and trailing whitespaces
data['Types'] = data['Types'].str.strip()

# number of unique types
unique_types = data['Types'].unique()
assert len(unique_types) >= 8

# find rows with nan
nan_rows = data[data['Types'].isnull()]
print(f'Number of rows with nan: {len(nan_rows)}')

# drop rows with nan
data.dropna(subset=['Types'], inplace=True)

# remove first column and Notes column
data.drop(columns='Unnamed: 0', inplace=True)
data.drop(columns='Notes', inplace=True)

# count of each type
type_counts = data['Types'].value_counts()
print(type_counts)


### 2. Split Data into Train and Test Set

# split data into train and test set with sklearn, 80% train, 20% test, ensure that test set is balanced
train_data, val_data = train_test_split(data, test_size=0.2, stratify=data['Types'], random_state=42)
type_counts_train = train_data['Types'].value_counts()
type_counts_val = val_data['Types'].value_counts()
print("Training data:")
print(type_counts_train)
print("")
print("Validation data:")
print(type_counts_val)

# plot distribution of types in train and val set
fig, ax = plt.subplots(1, 2, figsize=(12, 6))
ax[0].bar(type_counts_train.index, type_counts_train.values, color='skyblue')
ax[0].set_title('Train set')
ax[0].set_xlabel('Types')
ax[0].set_ylabel('Counts')
ax[0].grid(axis='y', linestyle='--', alpha=0.7)
ax[0].set_xticklabels(type_counts_train.index, rotation=45)
for i, v in enumerate(type_counts_train.values):
    ax[0].text(i, v, str(v), ha='center', va='bottom')
ax[1].bar(type_counts_val.index, type_counts_val.values, color='lightgreen')
ax[1].set_title('Validation set')
ax[1].set_xlabel('Types')
ax[1].set_ylabel('Counts')
ax[1].grid(axis='y', linestyle='--', alpha=0.7)
ax[1].set_xticklabels(type_counts_val.index, rotation=45)
for i, v in enumerate(type_counts_val.values):
    ax[1].text(i, v, str(v), ha='center', va='bottom')
plt.tight_layout()
plt.tight_layout()
plt.savefig('../../data/trainingdata_split.png')
plt.show()

# Save Train and Validation Data
train_data.to_excel('../../data/trainingdata_trainset.xlsx')
val_data.to_excel('../../data/trainingdata_valset.xlsx')


### 3. Convert Train and Test data for OpenAI Finetuning

# Define system prompt
prompt_system = (
    "You are analysing the relationships between text clauses and classifying them into one of eight sequencing categories:\n"
    "**Integrative (INT)** - Refers back to a stretch of text without nominalizing verbs or adjectives, utilizing demonstratives and third-person non-gendered pronouns.\n"
    "**Subsumptive (SUB)** - Involves referring back to text via the nominalization of a verb or adjective from the previous sentence, focusing on the action or quality itself.\n"
    "**Consequential (CON)** - Links passages through causal, conditional, or purposive connectors, indicating logical relationships..\n"
    "**Sequential (SEQ)** - Arranges meanings in a temporal or logical order using specific linking adverbs or conjunctions.\n"
    "**Incoherent (INC)** -  Connects unrelated passages, often starting with informal continuatives like 'ok' or 'now.'\n"
    "**Coherent (COH)** - Links passages smoothly using simple connectors like 'and' or 'while,' ensuring continuity.\n"
    "**Repetitive (REP)** - Repeats passages or clauses that are identically, without additional meaning.\n"
    "**Reiterative (REI)** - Repeats similar passages with slight variations to add meaning, often using phrases like 'that is' or 'in other words' to clarify or rephrase content.\n\n"     
    "Instructions:\n Given a text passage and two text clauses, classify the relationship between the two clauses into one of the eight categories above.\n"
    "You must only output the 3 character abbreviation of the class name ('INT', 'SUB', 'CON', 'SEQ', 'INC', 'COH', 'REP', 'REI').\n"
    "If the relationship between the two clauses is unclear, output 'NA' to indicate this.\n"
)

# Define prompt template          
prompt_temp = (
    "Provide the sequencing category that best describes the relationship between the two clauses:\n"
    "Clause 1: {clause1}\n"
    "Clause 2: {clause2}\n"
    "Text passage: {text_content}"
)

# save system prompt and query template to a file
with open('../../data/prompt_system.txt', 'w') as file:
    file.write(prompt_system)
with open('../../data/prompt_template.txt', 'w') as file:
    file.write(prompt_temp)

### Dict for abbreviation of sequence classes
sequence_classes = {
    'integrative': 'INT',
    'subsumptive': 'SUB',
    'consequential': 'CON',
    'sequential': 'SEQ',
    'incoherent': 'INC',
    'coherent': 'COH',
    'repetitive': 'REP',
    'reiterative': 'REI'
}

# generate list of queries and responses from train and val data
train_queries = []
train_responses = []
for index, row in train_data.iterrows():
    query = prompt_temp.format(clause1=row['Linked Chunk 1'], clause2=row['Linked Chunk 2'], text_content=row['Sequence'])
    train_queries.append(query)
    sequence_abr = sequence_classes[row['Types']]
    train_responses.append(sequence_abr)

val_queries = []
val_responses = []
for index, row in val_data.iterrows():
    query = prompt_temp.format(clause1=row['Linked Chunk 1'], clause2=row['Linked Chunk 2'], text_content=row['Sequence'])
    val_queries.append(query)
    sequence_abr = sequence_classes[row['Types']]
    val_responses.append(sequence_abr)


def create_finetuning_examples(system, queries, responses, outpath):
    """
    Create finetuning examples for OpenAI API from the training data.
    Save the examples to a jsonl file.

    :param system: str, system prompt
    :param queries: list, list of user queries
    :param responses: list, list of assistant responses
    :param outpath: str, path and filename to save the finetuning examples

    :return: list, list of finetuning examples
    """
    if len(queries) != len(responses):
        raise ValueError("All input lists must be of the same length")

    examples = []
    for query, response in zip(queries, responses):
        example = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": query},
                {"role": "assistant", "content": response}
            ]
        }
        examples.append(example)

    with open(outpath, 'w', encoding='utf-8') as file:
        for example in examples:
            file.write(json.dumps(example) + '\n')

    return examples


dataset_train = create_finetuning_examples(prompt_system, train_queries, train_responses, outpath=outpath_train)
dataset_val = create_finetuning_examples(prompt_system, val_queries, val_responses, outpath=outpath_val)


### 4. Data validation and cost estimates for finetuning

# Load the train dataset if not already loaded
if 'dataset_train' not in locals():
    with open(outpath_train, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    dataset_train = [json.loads(line) for line in lines]

# Load the val dataset
if 'dataset_val' not in locals():
    with open(outpath_val, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    dataset_val = [json.loads(line) for line in lines]\\\\

def validate_dataset(dataset):
    format_errors = defaultdict(int)

    for ex in dataset:
        if not isinstance(ex, dict):
            format_errors["data_type"] += 1
            continue
            
        messages = ex.get("messages", None)
        if not messages:
            format_errors["missing_messages_list"] += 1
            continue
            
        for message in messages:
            if "role" not in message or "content" not in message:
                format_errors["message_missing_key"] += 1
            
            if any(k not in ("role", "content", "name", "function_call") for k in message):
                format_errors["message_unrecognized_key"] += 1
            
            if message.get("role", None) not in ("system", "user", "assistant", "function"):
                format_errors["unrecognized_role"] += 1
                
            content = message.get("content", None)
            function_call = message.get("function_call", None)
            
            if (not content and not function_call) or not isinstance(content, str):
                format_errors["missing_content"] += 1
        
        if not any(message.get("role", None) == "assistant" for message in messages):
            format_errors["example_missing_assistant_message"] += 1

    if format_errors:
        print("Found errors:")
        for k, v in format_errors.items():
            print(f"{k}: {v}")
            return False
    else:
        return True


def num_tokens_from_messages(messages, tokens_per_message=3, tokens_per_name=1, encoding_name = "cl100k_base"):
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens

def num_assistant_tokens_from_messages(messages, encoding_name = "cl100k_base"):
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = 0
    for message in messages:
        if message["role"] == "assistant":
            num_tokens += len(encoding.encode(message["content"]))
    return num_tokens

def print_distribution(values, name):
    print(f"\n#### Distribution of {name}:")
    print(f"min / max: {min(values)}, {max(values)}")
    print(f"mean / median: {np.mean(values)}, {np.median(values)}")
    print(f"p5 / p95: {np.quantile(values, 0.1)}, {np.quantile(values, 0.9)}")


if validate_dataset(dataset_train):
    print("Train dataset is valid!")

if validate_dataset(dataset_val):
    print("Validation dataset is valid!")

# Calculate the number of tokens in each example
n_missing_system = 0
n_missing_user = 0
n_messages = []
convo_lens = []
assistant_message_lens = []
encoding = tiktoken.get_encoding("cl100k_base")

for ex in dataset_train:
    messages = ex["messages"]
    if not any(message["role"] == "system" for message in messages):
        n_missing_system += 1
    if not any(message["role"] == "user" for message in messages):
        n_missing_user += 1
    n_messages.append(len(messages))
    convo_lens.append(num_tokens_from_messages(messages))
    assistant_message_lens.append(num_assistant_tokens_from_messages(messages))
    
print("Num examples missing system message:", n_missing_system)
print("Num examples missing user message:", n_missing_user)
print_distribution(n_messages, "num_messages_per_example")
print_distribution(convo_lens, "num_total_tokens_per_example")
print_distribution(assistant_message_lens, "num_assistant_tokens_per_example")
n_too_long = sum(l > 4096 for l in convo_lens)
print(f"\n{n_too_long} examples may be over the 4096 token limit, they will be truncated during fine-tuning")

# Pricing and default n_epochs estimate
MAX_TOKENS_PER_EXAMPLE = 4096

n_epochs = 3
cost_per_token = 0.008/1000 # For GPT-3.5-turbo

n_billing_tokens_in_dataset = sum(min(MAX_TOKENS_PER_EXAMPLE, length) for length in convo_lens)
print(f"Dataset has ~{n_billing_tokens_in_dataset} tokens that will be charged for during training")
print(f"By default, you'll train for {n_epochs} epochs on this dataset")
print(f"By default, you'll be charged for ~{n_epochs * n_billing_tokens_in_dataset} tokens")
cost = cost_per_token * n_epochs * n_billing_tokens_in_dataset
print(f'Estimated cost for training is {round(cost,2)} USD.')
