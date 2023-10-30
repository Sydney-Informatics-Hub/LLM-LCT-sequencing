import panel as pn
from panel import Row

from annotation.controller import AnnotationController
from annotation.view.gui import Controls, LoadingIndicator, TextDisplay

pn.extension(notifications=True)


class AnnotationViewWrapper:
    def __init__(self, controller: AnnotationController):
        self.controller = controller

        self.loading_indicator = LoadingIndicator(controller)
        self.text_display = TextDisplay(controller)
        self.controls = Controls(controller)
        primary_row = Row(self.loading_indicator.get_component(),
                          self.text_display.get_component(),
                          self.controls.get_component())
        self.layout = primary_row

        self.controller.update_displays()

    def get_layout(self):
        return self.layout
