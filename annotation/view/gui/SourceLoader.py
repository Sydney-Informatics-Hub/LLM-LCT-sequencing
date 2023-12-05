from io import BytesIO
from typing import Optional

from panel import Row, Column
from panel.pane import Markdown
from panel.widgets import Button, FileInput, FileDownload, PasswordInput
from param import bind

from annotation.controller import AnnotationController


class FileUploadWidget:
    def __init__(self, file_description: str, filetypes: str):
        self.description = Markdown(f"**Choose {file_description} ({filetypes})**")
        self.file_input = FileInput(accept=filetypes, multiple=False)

        self.component = Row(self.description,
                             self.file_input,
                             sizing_mode="stretch_width",
                             align="start")

    def get_component(self):
        return self.component

    def get_file_content(self) -> Optional[BytesIO]:
        if self.file_input.value is not None:
            file_content = BytesIO()
            self.file_input.save(file_content)
            file_content.seek(0)
            return file_content

    def get_filetype(self) -> Optional[str]:
        if self.file_input.value is not None:
            filetype: str = self.file_input.filename.split('.')[-1]
            return filetype


class UnprocessedModeLoader:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller

        api_key_input = PasswordInput(name='Enter your OpenAI API Key (then press enter):',
                                           placeholder='<OpenAI API Key>')
        api_status = bind(self.write_api_key, api_key_input.param.value, watch=False)
        self.api_key_input = Row(api_key_input, Markdown(api_status))

        self.source_file_loader = FileUploadWidget("source file", ".docx,.txt")
        self.llm_definitions_loader = FileUploadWidget("LLM definitions [_Optional_]", ".xlsx")
        self.llm_examples_loader = FileUploadWidget("LLM examples [_Optional_]", ".xlsx")
        self.llm_prompt_loader = FileUploadWidget("LLM prompt [_Optional_]", ".txt")
        self.load_files_button = Button(name="Load files", button_type="success", button_style="outline")
        self.load_files_button.on_click(self.load_files)
        self.llm_process_button = Button(name="Process with LLM", button_type="success", button_style="solid", disabled=True)
        self.llm_process_button.on_click(self.llm_process_sequences)
        self.cost_time_estimate = Markdown("", height_policy="fit")

        self.download_preprocessed_modal = Row()

        self.component = Column(self.api_key_input,
                                self.source_file_loader.get_component(),
                                self.llm_definitions_loader.get_component(),
                                self.llm_examples_loader.get_component(),
                                self.llm_prompt_loader.get_component(),
                                Row(self.load_files_button,
                                    self.cost_time_estimate,
                                    self.llm_process_button
                                ),
                                self.download_preprocessed_modal)

    def get_component(self):
        return self.component

    def get_visible(self) -> bool:
        return self.component.visible

    def set_visible(self, visible: bool):
        self.component.visible = visible

    def write_api_key(self, key: str) -> str:
        if len(key) == 0:
            return "Please enter your OpenAI API Key."
        elif len(key) != 51:
            return "Incorrect API key provided. Must be 51 characters."
        else:
            success: bool = self.controller.set_api_key(key)
            if success:
                return "Valid API Key. Please continue."
            else:
                return "Error loading API key. Please try again."

    def _format_time_from_seconds(self, seconds: float) -> str:
        seconds = int(seconds)
        ratios: dict[str, float] = {
            "years": 31557600,
            "weeks": 604800,
            "days": 86400,
            "hours": 3600,
            "minutes": 60
        }

        formatted: str = ""
        for time_unit in ratios:
            multiples = seconds // ratios[time_unit]
            seconds -= multiples * ratios[time_unit]
            if multiples > 0:
                formatted += f"{multiples} {time_unit}, "
        formatted += f"{seconds} seconds"

        return formatted

    def set_cost_time_estimate(self):
        estimates: Optional[tuple[float, float]] = self.controller.get_cost_time_estimates()
        if estimates is None:
            self.cost_time_estimate.object = "..."
            return

        formatted_cost: str = f"${estimates[0]:.2f}"
        formatted_time: str = self._format_time_from_seconds(estimates[1])

        formatted_estimate = f"**Estimated Cost:** {formatted_cost}. **Estimated time:** {formatted_time}"
        self.cost_time_estimate.object = formatted_estimate

    def load_files(self, *_):
        source_file_content: Optional[BytesIO] = self.source_file_loader.get_file_content()
        if source_file_content is None:
            self.controller.display_error("No source file loaded")
            return
        source_filetype: Optional[str] = self.source_file_loader.get_filetype()

        llm_definitions_content: Optional[BytesIO] = self.llm_definitions_loader.get_file_content()
        llm_examples_content: Optional[BytesIO] = self.llm_examples_loader.get_file_content()
        llm_prompt_content: Optional[BytesIO] = self.llm_prompt_loader.get_file_content()

        self.set_cost_time_estimate()
        self.controller.load_source_file(source_file_content, source_filetype)
        self.controller.prepare_llm_processor(llm_definitions_content, llm_examples_content, llm_prompt_content)
        self.set_cost_time_estimate()

        self.llm_process_button.disabled = False

    def llm_process_sequences(self, *_):
        self.controller.llm_process_sequences()

        preprocessed_file_path: Optional[str] = self.controller.get_postprocess_file_path()
        self.download_preprocessed_modal.objects = [
            FileDownload(file=preprocessed_file_path, filename="llm_preprocessed.csv")]


class PreprocessedModeLoader:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller

        self.source_file_loader = FileUploadWidget("source file", ".docx,.txt")
        self.preprocessed_loader = FileUploadWidget("preprocessed sequences", ".csv")
        self.load_files_button = Button(name="Load",
                                        button_type="success", button_style="outline")
        self.load_files_button.on_click(self.load_files)

        self.component = Column(self.source_file_loader.get_component(),
                                self.preprocessed_loader.get_component(),
                                self.load_files_button)

    def get_component(self):
        return self.component

    def get_visible(self) -> bool:
        return self.component.visible

    def set_visible(self, visible: bool):
        self.component.visible = visible

    def load_files(self, *_):
        source_file_content: Optional[BytesIO] = self.source_file_loader.get_file_content()
        if source_file_content is None:
            self.controller.display_error("No source file loaded")
            return
        source_filetype: Optional[str] = self.source_file_loader.get_filetype()
        preprocessed_content: Optional[BytesIO] = self.preprocessed_loader.get_file_content()

        self.controller.load_source_file(source_file_content, source_filetype)
        self.controller.load_preprocessed_sequences(preprocessed_content)


class SourceLoader:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller

        self.unprocessed_mode_button = Button(name="Unprocessed mode",
                                              button_type="primary", button_style="outline")
        self.unprocessed_mode_button.on_click(self.toggle_unprocessed_mode)
        self.preprocessed_mode_button = Button(name="Preprocessed mode",
                                               button_type="primary", button_style="outline")
        self.preprocessed_mode_button.on_click(self.toggle_preprocessed_mode)

        self.unprocessed_mode_loader = UnprocessedModeLoader(self.controller)
        self.unprocessed_mode_loader.set_visible(False)
        self.preprocessed_mode_loader = PreprocessedModeLoader(self.controller)
        self.preprocessed_mode_loader.set_visible(False)

        self.component = Column(Row(self.unprocessed_mode_button,
                                    self.preprocessed_mode_button,
                                    sizing_mode="stretch_width",
                                    align="start"),
                                self.unprocessed_mode_loader.get_component(),
                                self.preprocessed_mode_loader.get_component())

    def get_component(self):
        return self.component

    def toggle_unprocessed_mode(self, *_):
        self.preprocessed_mode_button.button_style = "outline"

        if self.unprocessed_mode_loader.get_visible():
            self.unprocessed_mode_button.button_style = "outline"
            self.unprocessed_mode_loader.set_visible(False)
        else:
            self.unprocessed_mode_button.button_style = "solid"
            self.unprocessed_mode_loader.set_visible(True)
        self.preprocessed_mode_loader.set_visible(False)

    def toggle_preprocessed_mode(self, *_):
        self.unprocessed_mode_button.button_style = "outline"

        if self.preprocessed_mode_loader.get_visible():
            self.preprocessed_mode_button.button_style = "outline"
            self.preprocessed_mode_loader.set_visible(False)
        else:
            self.preprocessed_mode_button.button_style = "solid"
            self.preprocessed_mode_loader.set_visible(True)
        self.unprocessed_mode_loader.set_visible(False)
