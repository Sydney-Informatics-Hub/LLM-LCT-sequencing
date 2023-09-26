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
        self.controller.set_update_text_display_callable(self.update_text_display)

        self.text_display = TextDisplay()
        #####
        # TODO: Replace with controller bindings
        self.text_display.set_prev_paragraph_text(dummy_data.prev_para)
        self.text_display.set_next_paragraph_text(dummy_data.next_para)
        self.text_display.set_curr_paragraph_text(dummy_data.curr_para)
        #####
        self.controls = Controls()
        primary_row = Row(self.text_display.get_component(), self.controls.get_component())
        self.layout = primary_row

    def update_text_display(self):
        self.text_display.set_next_paragraph_text(self.controller.get_next_paragraph_text())
        self.text_display.set_prev_paragraph_text(self.controller.get_prev_paragraph_text())
        self.text_display.set_curr_paragraph_text(self.controller.get_curr_paragraph_text())
        clause_a_range, clause_b_range = self.controller.get_curr_sequence()
        self.text_display.set_clause_b_range(clause_a_range)
        self.text_display.set_clause_b_range(clause_b_range)

    def get_layout(self):
        return self.layout
