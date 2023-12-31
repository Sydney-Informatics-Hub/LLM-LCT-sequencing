# Load json schemas from files and return example dataframe and type definitions
import logging
import os
import json
import pandas as pd
from jsonschema import validate, ValidationError


# Load the JSON data
def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)


# Validate the JSON data against the schema
def validate_json(data, schema):
    """
    Validate the JSON data against the schema.

    Parameters
    ----------
    data : dict
        JSON data
    schema : dict
        JSON schema

    Returns
    -------
    bool
        True if the JSON data is valid, False otherwise
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        logging.error(f"JSON is invalid! Error: {e.message}")
        return False


def json_to_dataframe(data):
    """
    Convert the JSON data to a dataframe.

    Parameters
    ----------
    data : dict
        JSON data

    Returns
    -------
    df : pandas.DataFrame
    """
    rows = []
    for item in data['Data']:
        for example in item['Examples']:
            row = {
                'Type': item.get('Type', None),
                'Subtype': item.get('Subtype', None),
                'Sub_Subtype': item.get('Sub_Subtype', None),
                'Example': example.get('Example', None),
                'Linked_Chunk_1': example.get('Linked_Chunk_1', None),
                'Linked_Chunk_2': example.get('Linked_Chunk_2', None),
                'Reasoning': example.get('Reasoning', None),
                'Linkage_Word': example.get('Linkage_Word', None)
            }
            rows.append(row)
    df = pd.DataFrame(rows)
    return df


def json_to_dataframe_definitions(data):
    """
    Convert the JSON data to a dataframe.

    Parameters
    ----------
    data : dict
        JSON data

    Returns
    -------
    df : pandas.DataFrame
    """
    rows = []
    for item in data['Sequencing_Types']:
        row = {
            'Type': item.get('Type', None),
            'Subtype': None,
            'Sub_Subtype': None,
            'Description': item.get('Description', None),
        }
        rows.append(row)
        for subtype in item['Subtypes']:
            row = {
                'Type': item.get('Type', None),
                'Subtype': subtype.get('Subtype', None),
                'Sub_Subtype': None,
                'Description': subtype.get('Description', None),
            }
            rows.append(row)
            for subsubtype in subtype['Sub_Subtypes']:
                row = {
                    'Type': item.get('Type', None),
                    'Subtype': subtype.get('Subtype', None),
                    'Sub_Subtype': subsubtype.get('Sub_Subtype', None),
                    'Description': subsubtype.get('Description', None),
                }
                rows.append(row)
    df = pd.DataFrame(rows)
    return df


def main():
    # Load the JSON data and schema
    path_schema = "../schemas/"
    filename_examples = "sequencing_examples_reason.json"
    filename_schema = "schema_sequencing_examples_reason.json"
    filename_definitions = "sequencing_types.json"

    logging.debug("Loading sequencing type definitions...")
    sequencing_definitions = load_json(os.path.join(path_schema, filename_definitions))
    # print all itmes in the sequencing_definitions list Sequencing_Types
    logging.debug("----------------- Sequencing Types ---------------------")
    logging.debug(json.dumps(sequencing_definitions, indent=2))
    logging.debug("--------------------------------------------------------")

    logging.debug("Loading examples...")
    examples = load_json(os.path.join(path_schema, filename_examples))
    schema = load_json(os.path.join(path_schema, filename_schema))

    # Validate the JSON data against the schema
    if validate_json(examples, schema):
        df = json_to_dataframe(examples)
        logging.debug(df)


if __name__ == "__main__":
    main()
