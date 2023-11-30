from pathlib import Path

from .AnnotationDAO import AnnotationDAO
from .DatastoreHandler import DatastoreHandler

_file_directory: Path = Path(__file__).resolve().parent

llm_data_store_dir: Path = _file_directory.joinpath("llm_data_store/")

_data_store_path: Path = _file_directory.joinpath("data_store/")
ref_text_ds_path: Path = _data_store_path.joinpath("reference_text.txt")
clauses_ds_path: Path = _data_store_path.joinpath("clauses.csv")
sequences_ds_path: Path = _data_store_path.joinpath("sequences.csv")
pre_llm_sequence_path: Path = _data_store_path.joinpath("pre_llm_sequences.csv")
