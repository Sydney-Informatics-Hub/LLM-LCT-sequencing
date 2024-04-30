# prepare training data

import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

file_path = '../../data/trainingdata.xlsx'

### Data Read-in and Cleaning

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



### Split Data into Train and Test Set

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


### Convert Train and Test data for OpenAI Finetuning

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


def create_finetuning_examples(systems, queries, responses):
    """
    Create finetuning examples for OpenAI API from the training data.

    :param systems: list, list of system prompts
    :param queries: list, list of user queries
    :param responses: list, list of assistant responses

    :return: list, list of finetuning examples
    """
    if len(systems) != len(queries) or len(queries) != len(responses):
        raise ValueError("All input lists must be of the same length")

    examples = []
    for system, query, response in zip(systems, queries, responses):
        example = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": query},
                {"role": "assistant", "content": response}
            ]
        }
        examples.append(example)

    return examples


### Upload Data to OpenAI
from openai import OpenAI
client = OpenAI()

client.files.create(
  file=open("mydata.jsonl", "rb"),
  purpose="fine-tune"
)



