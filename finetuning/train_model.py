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

fname_train_openai = '../../data/data_openai_train.jsonl'
fname_val_openai = '../../data/data_openai_val.jsonl'

fname_train_df = '../../data/trainingdata_trainset.xlsx'
fname_val_df = '../../data/trainingdata_valset.xlsx'


with open(os.path.expanduser("../../openai_key.txt")) as f:
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

# Create a fine-tuned mode
job = client.fine_tuning.jobs.create(
  training_file=train_id, 
  validation_file=val_id,
  model="gpt-3.5-turbo",
  hyperparameters={"n_epochs": 3}
)
job_id = job.id
print("job ID:", job_id)

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
elif status.status == "running":
    print("Model is not ready yet, try again later")
else:
    print('status:', status.status)



