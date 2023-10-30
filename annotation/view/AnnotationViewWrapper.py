import panel as pn
from panel import Row

from annotation.controller import AnnotationController
from annotation.view.global_notifiers import LoadingIndicator
from annotation.view.gui import Controls, TextDisplay

pn.extension(notifications=True)


class AnnotationViewWrapper:
    def __init__(self, controller: AnnotationController):
        self.controller = controller

        self.loading_indicator = LoadingIndicator(controller)
        self.text_display = TextDisplay(controller)
        self.controls = Controls(controller)
        self.layout = Row(self.loading_indicator.get_component(),
                          self.text_display.get_component(),
                          self.controls.get_component())

        self.controller.update_displays()

    def get_layout(self):
        return self.layout
