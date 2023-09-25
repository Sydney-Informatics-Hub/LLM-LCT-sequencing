import panel as pn
from panel import Row, Column
from panel.widgets import StaticText, Button

from annotation.controller.AnnotationController import AnnotationController
from annotation.view import dummy_data
from annotation.view.gui.widgets.TextDisplay import TextDisplay

pn.extension()


class AnnotationViewWrapper:
    def __init__(self, controller: AnnotationController):
        self.controller = controller
        self.widgets = self.construct_widgets()

    def construct_widgets(self):
        text_display = TextDisplay()
        #####
        # TODO: Replace with controller bindings
        text_display.set_prev_paragraph(dummy_data.prev_para)
        text_display.set_next_paragraph(dummy_data.next_para)
        text_display.set_curr_paragraph(dummy_data.curr_para)
        text_display.set_clause_a_range([0, 35])
        # text_display.set_clause_b_range([104, 128])
        text_display.set_clause_b_range([20, 55])
        #####

        paragraph_controls = Row(
            Button(name="Previous", button_type="primary"),
            StaticText(value="1"),
            Button(name="Next", button_type="primary"),
            sizing_mode="stretch_width"
        )
        paragraph_widget = Column(
            StaticText(value="Paragraph"),
            paragraph_controls
        )
        controls = Column(paragraph_widget)
        primary_row = Row(text_display.get_widget(), controls)
        return primary_row

    def get_widgets(self):
        return self.widgets
