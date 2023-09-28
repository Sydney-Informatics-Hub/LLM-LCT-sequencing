import panel as pn
from panel import Row, Column
from panel.widgets import StaticText, Button

from annotation.controller.AnnotationController import AnnotationController
from annotation.view import dummy_data
from annotation.view.gui.widgets.Controls import Controls
from annotation.view.gui.widgets.TextDisplay import TextDisplay

pn.extension()


class AnnotationViewWrapper:
    def __init__(self, controller: AnnotationController):
        self.controller = controller

        self.text_display = TextDisplay(controller)
        #####
        # TODO: Replace with controller bindings
        # self.text_display.set_prev_paragraph_text(dummy_data.prev_para)
        # self.text_display.set_next_paragraph_text(dummy_data.next_para)
        # self.text_display.set_curr_paragraph_text(dummy_data.curr_para)
        # self.text_display.set_clause_a_range((0, 40))
        # self.text_display.set_clause_b_range((30, 50))
        #####
        self.controls = Controls(controller)
        primary_row = Row(self.text_display.get_component(), self.controls.get_component())
        self.layout = primary_row

        self.controller.update_displays()

    def get_layout(self):
        return self.layout
