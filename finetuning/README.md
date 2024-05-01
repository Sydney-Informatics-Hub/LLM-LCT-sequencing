# Fine-tuning of a Custom LCT OpenAI Model

This repository contains multiple scripts that assist in the fine-tuning of a model for LCT sequencing classification.

The primary steps for fine-tuning a model are:
1. **Data Aggregation**: Combine, clean, and inspect data.
2. **Data Augmentation** (optional): Generate synthetic data with an LLM if classes are unbalanced or data is insufficient.
3. **Data Preparation**: Split data into training and validation sets; convert to the OpenAI format.
4. **Model Training**: Set up the model configuration and data files for submission to the OpenAI fine-tuning API.
5. **Model Evaluation**: Test the model on the validation set, generate a confusion matrix, and compute classification metrics.

The scripts facilitating the fine-tuning pipeline include:
- **synthetic data generation**: Refer to sequencing class prompts in the 'prompts' folder (these prompts can be executed in any LLM environment, e.g., GPT-4).
- **synthetic_to_excel.py**: Converts the output from synthetic data generation to data tables for expert review.
- **plot_training_data.py**: Plots the distribution of training data.
- **prepare_training_data.py**, which includes:
    1. Data loading and cleaning.
    2. Splitting data into training and test sets.
    3. Converting data for OpenAI fine-tuning.
    4. Validating data and estimating costs for fine-tuning.
- **train_model.py**, which includes:
    1. Uploading data to OpenAI and setting up the fine-tuning configuration.
    2. Submitting the fine-tuning job.
    3. Saving results.
    4. Testing on validation data.
    5. Evaluation, including the generation of a confusion matrix and a detailed classification report.

All model details and results will be saved in the specified output folder.

Installation dependencies are listed in the Conda environment file: `env_lct_finetuning.yaml`.

For more information about fine-tuning an OpenAI model, refer to the [OpenAI fine-tuning documentation](https://platform.openai.com/docs/guides/fine-tuning/use-a-fine-tuned-model) and the [LLM Fine-tuning Seminar Notebook](https://github.com/Sydney-Informatics-Hub/LLM-finetuning-seminar/blob/main/notebook/LLM_finetuning_seminar.ipynb).