# Python tool to export and import excel files to and from the json
from os.path import dirname, abspath

import pandas as pd
import json

import matplotlib.pyplot as plt
import seaborn as sns

from .load_schema_json import load_json, validate_json, json_to_dataframe, json_to_dataframe_definitions


parent_dir = dirname(dirname(abspath(__file__)))
schema_dir = parent_dir + "/schemas/"

def excel_to_json(excel_filename, json_filename_out):
    """
    Convert the Excel file to JSON data.

    Parameters
    ----------
    excel_filename : str
        Input Excel filename
    json_filename : str
        JSON filename
    """
    df = pd.read_excel(excel_filename)
    if df.shape[1] >= 6:
        data_dict = dataframe_to_json(df)
    else:
        data_dict = dataframe_to_json_definitions(df)

    # write dict to json
    data_json = json.dumps(data_dict, indent=2)

    # replace NaN with None
    data_json = data_json.replace('NaN', 'null')

    # write json to file
    with open(json_filename_out, 'w') as f:
        f.write(data_json)

    if df.shape[1] >= 6:
       # validate the data
       json_schema = schema_dir + "schema_sequencing_examples_reason.json"
       schema = load_json(json_schema)
       data_loaded = load_json(json_filename_out)
       assert validate_json(data_loaded, schema), "JSON data is invalid!"



def dataframe_to_json(df):
    """
    converts dataframe to json

    Parameters
    ----------
    df : pandas.DataFrame
        dataframe to convert

    Returns
    -------
    data : dict
        JSON data
    """
    data = {}
    data['Data'] = []
    # group by type, subtype, subsubtype
    df = df.groupby(['Type', 'Subtype', 'Sub_Subtype'])
    # iterate through the groups
    for name, group in df:
        item = {}
        item['Type'] = name[0]
        item['Subtype'] = name[1]
        item['Sub_Subtype'] = name[2]
        item['Examples'] = []
        # iterate through the rows in the group
        for index, row in group.iterrows():
            example = {}
            example['Example'] = row['Example']
            example['Reasoning'] = row['Reasoning']
            example['Linked_Chunk_1'] = row['Linked_Chunk_1']
            example['Linked_Chunk_2'] = row['Linked_Chunk_2']
            example['Linkage_Word'] = row['Linkage_Word']
            item['Examples'].append(example)
        data['Data'].append(item)
    return data


def dataframe_to_json_definitions(df):
    """
    Converts dataframe to json for the sequencing definitions.

    Parameters
    ----------
    df : pandas.DataFrame
        dataframe to convert

    Returns
    -------
    data : dict
        JSON data
    """
    result = {'Sequencing_Types': []}

    for _, row in df.iterrows():
        type_name = row['Type']
        subtype_name = row['Subtype']
        subsubtype_name = row['Sub_Subtype']
        description = row['Description']

        type_dict = next((item for item in result['Sequencing_Types'] if item['Type'] == type_name), None)
        if not type_dict:
            type_dict = {'Type': type_name}
            result['Sequencing_Types'].append(type_dict)

        if pd.notna(subtype_name):
            if 'Subtypes' not in type_dict:
                type_dict['Subtypes'] = []
            subtype_dict = next((item for item in type_dict['Subtypes'] if item['Subtype'] == subtype_name), None)
            if not subtype_dict:
                subtype_dict = {'Subtype': subtype_name}
                type_dict['Subtypes'].append(subtype_dict)
        else:
            type_dict['Description'] = description
            continue

        if pd.notna(subsubtype_name):
            if 'Sub_Subtypes' not in subtype_dict:
                subtype_dict['Sub_Subtypes'] = []
            subsubtype_dict = {'Sub_Subtype': subsubtype_name, 'Description': description}
            subtype_dict['Sub_Subtypes'].append(subsubtype_dict)
        else:
            subtype_dict['Description'] = description

    return result


def json_to_excel(
    json_filename, 
    excel_filename, 
    json_schema = schema_dir + "schema_sequencing_examples_reason.json"):
    """
    Convert the JSON data to an Excel file.

    Parameters
    ----------
    json_filename : str
        JSON filename
    excel_filename : str
        Output Excel filename
    json_schema : str
    """
    data = load_json(json_filename)
    schema = load_json(json_schema)

    assert validate_json(data, schema), "JSON data is invalid!"
    
    df = json_to_dataframe(data)
    
    #df.to_excel(excel_filename, index=False)
    write_excel_formatting(df, excel_filename)


def json_to_excel_definitions(
    json_filename, 
    excel_filename):
    """
    Convert the JSON data to an Excel file.

    Parameters
    ----------
    json_filename : str
        JSON filename for definitions
    excel_filename : str
        Output Excel filename for definitions
    """
    data = load_json(json_filename)
    
    df = json_to_dataframe_definitions(data)
    df = df[['Type', 'Subtype', 'Sub_Subtype', 'Description']]
    
    #df.to_excel(excel_filename, index=False)
    write_excel_formatting(df, excel_filename)


def write_excel_formatting(df, path):
    """ Create a writer object with excel formatting

    Parameters
    ----------
    df : pandas.DataFrame
    path : str, output path for the excel file
    """

    # Create a writer object
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
        
        # Access the openpyxl worksheet object
        worksheet = writer.sheets['Sheet1']
        
        # Get openpyxl objects for styles
        from openpyxl.styles import PatternFill, Font
        
        # Define header format
        header_fill = PatternFill(start_color='D7E4BC', end_color='D7E4BC', fill_type='solid')
        header_font = Font(bold=True)
        
        # Apply formatting to headers
        for cell in worksheet["1:1"]:
            cell.fill = header_fill
            cell.font = header_font
        
        # Set column widths (adjust as necessary)
        if df.shape[1] >= 6:
            col_widths = {
                'A': 22,
                'B': 22,
                'C': 22,
                'D': 80,
                'E': 80,
                'F': 20
            }
        else:
            col_widths = {
                'A': 22,
                'B': 22,
                'C': 22,
                'D': 140,
            }
        for col, width in col_widths.items():
                worksheet.column_dimensions[col].width = width


def plot_classes(json_filename, fname_out):
    """
    Plot histogram of the occurence of sub and sub-subtype classes in the dataframe.

    Parameters
    ----------
    fname_json : str
        input json filename
    fname_out : str
        output filename
    """
    data = load_json(json_filename)
    df = json_to_dataframe(data)

    # generate two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    # histogram of sub-subtypes
    sns.countplot(x='Sub_Subtype', data=df, ax=ax1)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90)
    ax1.set_title('Sub-Subtype')
    # histogram of subtypes
    sns.countplot(x='Subtype', data=df, ax=ax2)
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=90)
    ax2.set_title('Subtype')
    plt.tight_layout()
    plt.savefig(fname_out, dpi=300)
    # close the figure
    plt.close(fig)


def test_json_to_excel():
    """
    Test json_to_excel().
    """
    json_filename = schema_dir + "sequencing_examples_reason.json"
    excel_filename = schema_dir + "sequencing_examples_reason.xlsx"
    json_to_excel(json_filename, excel_filename)


def test_excel_to_json():
    """
    Test json_to_excel().
    """
    
    excel_filename = schema_dir + "sequencing_examples_reason.xlsx"
    json_filename_out = schema_dir + "sequencing_examples_reason_recovered.json"
    excel_to_json(excel_filename, json_filename_out)


def test_json_to_excel_definitions():
    json_to_excel_definitions(schema_dir + "sequencing_types.json", schema_dir + "sequencing_types.xlsx")


def test_excel_to_json_definitions():
    excel_to_json(schema_dir + "sequencing_types.xlsx", schema_dir + "sequencing_types_recovered.json")
