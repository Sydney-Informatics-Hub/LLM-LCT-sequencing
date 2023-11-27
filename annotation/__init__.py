from pathlib import Path

_file_directory: Path = Path(__file__).parent.resolve()

log_file_path: Path = _file_directory.joinpath(".log.txt")
llm_definitions_path: Path = _file_directory.parent.joinpath("schemas/sequencing_types.xlsx")
llm_examples_path: Path = _file_directory.parent.joinpath("tests/sequencing_examples.xlsx")
llm_zero_prompt_path: Path = _file_directory.parent.joinpath("schemas/instruction_multiprompt.txt")
