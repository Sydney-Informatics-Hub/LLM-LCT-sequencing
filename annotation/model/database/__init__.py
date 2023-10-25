from os.path import dirname, realpath

from .AnnotationDAO import AnnotationDAO
from .DatastoreBuilder import DatastoreBuilder


_data_store_path: str = dirname(realpath(__file__)) + "/data_store/"
ref_text_ds_path: str = _data_store_path + "reference_text.txt"
clauses_ds_path: str = _data_store_path + "clauses.csv"
sequences_ds_path: str = _data_store_path + "sequences.csv"
