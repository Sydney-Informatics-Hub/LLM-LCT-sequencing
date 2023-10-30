from io import BytesIO

from panel import Row
from panel.widgets import FileInput, Button

from annotation.controller import AnnotationController


class FileUploadWidget:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller

        self.file_input = FileInput(accept=".docx", multiple=False)
        self.load_file_button = Button(name="Load file", button_type="success", button_style="outline")
        self.load_file_button.on_click(self.load_file)

        self.component = Row(self.file_input,
                             self.load_file_button,
                             align="start")

    def get_component(self):
        return self.get_component()

    def load_file(self, *args):
        if self.file_input.value is None:
            self.controller.display_error("No file loaded")
        else:
            file_content = BytesIO()
            self.file_input.save(file_content)
            self.controller.load_source_file(file_content)
