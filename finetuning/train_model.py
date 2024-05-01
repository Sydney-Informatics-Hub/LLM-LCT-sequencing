"""
Finetune OpenAI model with custom dataset.

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
    'incoherent': 'INC',
    'coherent': 'COH',
    'repetitive': 'REP',
    'reiterative': 'REI'
}

# add incremental version vx to path_model, add 1 to the last version
# get the last version
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
# Your fine-tuning job ftjob-PVko8HAPBBCjHVvRMoqlH3Sg has successfully completed, and a new model ft:gpt-3.5-turbo-0125:personal::9JcKFSbA has been created for your use. 

result_file_content = client.files.retrieve(model_result_files[0])

#### Validate model
print(result_file_content)
result_filename = result_file_content.filename

# download file
# from: https://api.openai.com/v1/files/{file_id}/content
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

