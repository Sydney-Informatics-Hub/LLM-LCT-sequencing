import panel as pn
from panel import Row, Column

from annotation.controller import AnnotationController
from annotation.view.global_notifiers import LoadingIndicator
from annotation.view.gui import Controls, TextDisplay, SourceLoader
from annotation.view.gui.styles import main_column_style, top_bar_style

pn.extension(notifications=True)


class AnnotationViewWrapper:
    def __init__(self, controller: AnnotationController):
        self.controller = controller

        self.loading_indicator = LoadingIndicator(controller)
        self.source_loader = SourceLoader(controller)
        self.text_display = TextDisplay(controller)
        self.controls = Controls(controller)
        self.layout = Column(Row(self.source_loader.get_component(),
                                 self.loading_indicator.get_component(),
                                 styles=top_bar_style,
                                 sizing_mode='stretch_width'),
                             Row(self.text_display.get_component(),
                                 self.controls.get_component(),
                                 sizing_mode='stretch_width'),
                             styles=main_column_style,
                             sizing_mode='stretch_width')

        self.controller.update_displays()

    def get_layout(self):
        return self.layout
