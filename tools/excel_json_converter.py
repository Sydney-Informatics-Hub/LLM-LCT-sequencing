# Python tool to export and import excel files to and from the json

import pandas as pd
import os

from load_schema_json import load_json, validate_json, json_to_dataframe
from openpyxl.styles import PatternFill, Border, Side, Font

def json_to_excel(
    json_filename, 
    excel_filename, 
    json_schema =  "../schemas/schema_sequencing_examples_reason.json"):
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
        col_widths = {
            'A': 20,
            'B': 20,
            'C': 20,
            'D': 80,
            'E': 80,
            'F': 20
        }
        for col, width in col_widths.items():
            worksheet.column_dimensions[col].width = width



def test_json_to_excel():
    """
    Test json_to_excel().
    """
    json_filename = "../schemas/sequencing_examples_reason.json"
    excel_filename = "../schemas/sequencing_examples_reason.xlsx"
    json_to_excel(json_filename, excel_filename)