import json
import pandas as pd
import os

inpath = '../../data/finetuning/'
filenames = ['synth_incoherent.json', 'synth_integrative.json', 'synth_repetitive.json', 'synth_subsumptive.json']
types = ['incoherent', 'integrative', 'repetitive', 'subsumptive']


def convert2excel(inpath, filenames, types):
    """
    read each json file and convert to DataFrame. Then concatente all DataFrames and save to excel file.

    :param inpath: str, path to the directory containing the json files
    :param filenames: list, list of json files to be converted
    :param types: list, list of types corresponding to the json files
    
    """
    dfs = []
    for filename, type in zip(filenames, types):
        file_path = os.path.join(inpath, filename)
        with open(file_path, 'r') as file:
            data = json.load(file)
        df = pd.DataFrame(data)
        df.drop(columns='Reasoning', inplace=True)
        df['Type'] = type
        dfs.append(df)
    df = pd.concat(dfs)
    df['Origin'] = 'synthetic'
    output_path = os.path.join(inpath, 'synth_all.xlsx')
    df.to_excel(output_path, index=False)
    print(f'Data saved to {output_path}')


