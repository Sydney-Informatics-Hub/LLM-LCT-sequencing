"""
Script for finetuning OpenAI model with custom dataset and evaluation of model.

All results are saved in the directory: outpath_model (set paths and filenames below)

Prerequisites: formatted trainig and validation dataset in jsonl format.
(see for dataset preparation: prepare_training_data.py)

Note that the finetuning requires the latest version of the openai library, which is not available in the current LCT environment.
For finetuning create a new environment with the required libraries: see requirements_finetuning.txt

or change to conda env "lct_finetuning" if installed
"""

import os
import json
import openai
import pandas as pd
from openai import OpenAI
import requests
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import classification_report

### Settings 

# Paths to training and validation data in OpenAI format
fname_train_openai = '../../data/data_openai_train.jsonl'
fname_val_openai = '../../data/data_openai_val.jsonl'

# Paths to training and validation data in DataFrame format and with ground truth
fname_train_df = '../../data/trainingdata_trainset.xlsx'
fname_val_df = '../../data/trainingdata_valset.xlsx'

# Paths to prompt system and query
fname_prompt_system = '../../data/prompt_system.txt'
fname_prompt_query = '../../data/prompt_query.txt'

outpath_model = '../../data/finetuning/models/'

fname_openai_key = os.path.expanduser("../../openai_key.txt")


### Dict for abbreviation of sequence classes
sequence_classes = {
    'integrative': 'INT',
    'subsumptive': 'SUB',
    'consequential': 'CON',
    'sequential': 'SEQ',
    'reiterative': 'REI',
    'repetitive': 'REP',
    'coherent': 'COH',
    'incoherent': 'INC',
}

# add incremental version vx to path_model, add 1 to the last version
versions = [int(f.split('v')[-1]) for f in os.listdir(outpath_model) if f.startswith('v')]
if versions:
    version = max(versions) + 1
else:
    version = 1
outpath_model = os.path.join(outpath_model, f'v{version:02d}')
os.makedirs(outpath_model, exist_ok=True)

# copy training and validation data to the model directory
if not os.path.isfile(os.path.join(outpath_model, os.path.basename(fname_train_openai))):
    os.system(f'cp {fname_train_openai} {outpath_model}')
if not os.path.isfile(os.path.join(outpath_model, os.path.basename(fname_val_openai))):
    os.system(f'cp {fname_val_openai} {outpath_model}')
# copy also the training and validation data in DataFrame format
if not os.path.isfile(os.path.join(outpath_model, os.path.basename(fname_train_df))):
    os.system(f'cp {fname_train_df} {outpath_model}')
if not os.path.isfile(os.path.join(outpath_model, os.path.basename(fname_val_df))):
    os.system(f'cp {fname_val_df} {outpath_model}')


# initiate OpenAI client
with open(fname_openai_key) as f:
    openai.api_key = f.read().strip()
client = OpenAI(api_key = openai.api_key)


# Upload training and validation data to OpenAI
response_train = client.files.create(
  file=open(fname_train_openai, "rb"),
  purpose="fine-tune"
)
train_id = response_train.id

response_val = client.files.create(
  file=open(fname_val_openai, "rb"),
  purpose="fine-tune"
)
val_id = response_val.id

print("train ID:", train_id)
# train ID: file-46PiKIkk29q5eiDFLNAPTjhH
print("val ID:", val_id)
# val ID: file-z0uHUloR2pvyr8OemMhu0wgj

# Create a fine-tuned mode
job = client.fine_tuning.jobs.create(
  training_file=train_id, 
  validation_file=val_id,
  model="gpt-3.5-turbo",
  hyperparameters={"n_epochs": 3}
)
job_id = job.id
print("job ID:", job_id)
# job ID: ftjob-PVko8HAPBBCjHVvRMoqlH3Sg

# if job needs to be cancelled:
#client.fine_tuning.jobs.cancel(job_id)


# Check status. Note: you will also receive email notification when the job is done
status = client.fine_tuning.jobs.retrieve(job_id)
if status.status == "succeeded":
    print("Model is ready for use!")
    model_id = status.id
    model_runtime = status.finished_at - status.created_at
    model_trained_tokens = status.trained_tokens
    model_hyperparams = status.hyperparameters
    model_name = status.fine_tuned_model
    model_result_files = status.result_files
    print(f"Model name: {model_name}")
    print(f"Model runtime: {model_runtime} seconds")
    print(f"Model trained tokens: {model_trained_tokens}")
    print(f"Model hyperparameters: {model_hyperparams}")
    print(f"Model result files: {model_result_files}")
    print(f"Time to completion: {(status.finished_at - status.created_at)/60:.2f} minutes") 
    #  27.63 minutes
elif status.status == "running":
    print("Model is not ready yet, try again later")
else:
    print('status:', status.status)


model_name = status.fine_tuned_model
# 'ft:gpt-3.5-turbo-0125:personal::9JcKFSbA'

result_file_content = client.files.retrieve(model_result_files[0])

#### Validate model
print(result_file_content)
result_filename = result_file_content.filename

# download file
url = f"https://api.openai.com/v1/files/{result_file_content.id}/content"
r = requests.get(url, headers={"Authorization": f"Bearer {openai.api_key}"})
if r.status_code == 200:
    with open(os.path.join(outpath_model,result_filename), "wb") as f:
        f.write(r.content)
    print(f"Downloaded result file to {result_filename}")

# Save model information to a json file
model_dict = status.dict()
fname_model_info = os.path.join(outpath_model,'model_info.json')
with open(os.path.join(fname_model_info), 'w') as f:
    json.dump(model_dict, f, indent=4)


# Analyse finetuning job performance
df_metrics = pd.read_csv(result_filename)
df_metrics.dropna(inplace=True)
# plot 'train_loss' and 'valid_loss' vs 'step' as line plot
plt.figure(figsize=(10, 6))
plt.plot(df_metrics['step'], df_metrics['train_loss'], label='train_loss', color='skyblue')
plt.plot(df_metrics['step'], df_metrics['valid_loss'], label='valid_loss', color='salmon')
plt.xlabel('step')
plt.ylabel('loss')
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(outpath_model,'loss_vs_step.png'))
plt.show()


### Prediction and Evaluation of the Model

def query_gptmodel(clause1, 
                   clause2, 
                   text_content, 
                   prompt_template, 
                   prompt_system, 
                   model_name):
    """
    Query the GPT model with the given clauses and text content.

    Parameters:
    ----------
    - clause1 (str): The first clause.
    - clause2 (str): The second clause.
    - text_content (str): The text content.
    - prompt_template (str): The template for the query.
    - prompt_system (str): The system prompt.
    - model_name (str): The name of the finetuned model.

    Returns:
    ----------
    - str: The predicted type.
    - float: Log probability of the prediction.
    """
    query = prompt_template.format(clause1=clause1, clause2=clause2, text_content=text_content)
    response = client.chat.completions.create(
    model=model_name,
    messages=[
      {"role": "system", "content": prompt_system},
      {"role": "user", "content": query},
    ],
    temperature=0.0,
    max_tokens=2,
    logprobs = True)
    return response.choices[0].message.content, response.choices[0].logprobs.content[0].logprob


# read fname_prompt_system and fname_prompt_query
with open(fname_prompt_system, 'r') as f:
    prompt_system = f.read()
with open(fname_prompt_query, 'r') as f:
    prompt_query = f.read()

### Evaluation of the model
# system prompt = ~415 tokens, reponse = 1 token
# read fname_val_df
df_val = pd.read_excel(fname_val_df)
# generate result dataframe
df_results = df_val[['Linked Chunk 1', 'Linked Chunk 2', 'Sequence', 'Types']].copy()
df_results.rename(columns={'Types': 'True Type'}, inplace=True)
df_results['Predicted Type'] = None
df_results['Correct'] = None
df_results['True Type']= df_results['True Type'].apply(lambda x: sequence_classes[x])
df_results['Confidence'] = None
# iterate over the validation dataset and evaluate the model
for idx, row in df_results.iterrows():
    clause1 = row['Linked Chunk 1']
    clause2 = row['Linked Chunk 2']
    text_content = row['Sequence']
    type_true = row['True Type']
    type_pred, conf = query_gptmodel(clause1, clause2, text_content, prompt_query, prompt_system, model_name)
    print(f"True type: {type_true}, Predicted type: {type_pred}  Correct: {type_true == type_pred}")
    df_results.loc[idx, 'Predicted Type'] = type_pred
    df_results.loc[idx, 'Correct'] = type_true == type_pred
    df_results.loc[idx, 'Confidence'] = round(np.exp(conf),6)

# save the results to a file
fname_results = os.path.join(outpath_model, 'results_eval.xlsx')
df_results.to_excel(fname_results, index=False)


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
    matrix = matrix.reindex(index=class_labels, columns=class_labels, fill_value=0)

    # plot matrix
    plt.figure(figsize=(10, 7))
    sns.heatmap(matrix, annot=True, cmap='Blues', fmt='g')
    plt.savefig(outfname_plot, dpi=300)
    if plot_show:
        plt.show()
    return matrix



seq_classes = list(sequence_classes.keys())
class_labels = [sequence_classes[seq_class] for seq_class in seq_classes]
classes_test = df_results['True Type'].values
classes_pred = df_results['Predicted Type'].values
outfname_plot = os.path.join(outpath_model, 'confusion_matrix.png')
confusion_matrix = gen_confusion_matrix(classes_test, classes_pred, class_labels, outfname_plot)


class_report = classification_report(classes_test, classes_pred, target_names=class_labels, output_dict=True)
# print classification report with pandas
df_class_report = pd.DataFrame(class_report).transpose()
print(df_class_report)
df_class_report.to_excel(os.path.join(outpath_model, 'classification_report.xlsx'), index=True)
# Calculate the accuracy and precision
accuracy = df_results['Correct'].mean()
print(f"Mean Accuracy: {accuracy:.2f}")


"""
### To do: plot the confusion matrix
calculate other metrics

- for finetuning check for output token size is 1
- check finetuning parameters for longer training given that performance did not stabilize
- check confusion metrics and metrics where to add more data --> REI low
- create env file for lct_finetuning
- add batch processing for predictions

"""


