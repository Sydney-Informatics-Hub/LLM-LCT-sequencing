import panel as pn
from panel import Row

from annotation.controller.AnnotationController import AnnotationController
from annotation.view.gui.widgets.Controls import Controls
from annotation.view.gui.widgets.TextDisplay import TextDisplay

pn.extension()


class AnnotationViewWrapper:
    def __init__(self, controller: AnnotationController):
        self.controller = controller

        self.text_display = TextDisplay(controller)
        self.controls = Controls(controller)
        primary_row = Row(self.text_display.get_component(), self.controls.get_component())
        self.layout = primary_row

        self.controller.update_displays()

    def get_layout(self):
        return self.layout
