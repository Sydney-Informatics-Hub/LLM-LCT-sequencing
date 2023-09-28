from panel import Row, Column
from panel.widgets import Button
from panel.pane import Str

from annotation.controller.AnnotationController import AnnotationController
from .styles import controls_style, paragraph_heading_style, controls_navigation_button_style, paragraph_id_style


class ParagraphControls:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller
        self.title = Str("Paragraph", styles=paragraph_heading_style)
        self.curr_paragraph_id = Str("1", styles=paragraph_id_style)
        self.prev_paragraph_button = Button(name="\N{LEFTWARDS ARROW TO BAR} Previous", styles=controls_navigation_button_style)
        self.prev_paragraph_button.on_click(self.prev_paragraph)
        self.next_paragraph_button = Button(name="Next \N{RIGHTWARDS ARROW TO BAR}", styles=controls_navigation_button_style)
        self.next_paragraph_button.on_click(self.next_paragraph)

        self.component = Column(
            self.title,
            Row(
                self.prev_paragraph_button,
                self.curr_paragraph_id,
                self.next_paragraph_button,
                sizing_mode="stretch_width"
            ),
            sizing_mode="stretch_width"
        )

        self.controller.add_update_text_display_callable(self.update_display)

    def get_component(self):
        return self.component

    def update_display(self):
        self.curr_paragraph_id.object = str(self.controller.get_current_paragraph_id())

    def next_paragraph(self, event):
        self.controller.next_paragraph()

    def prev_paragraph(self, event):
        self.controller.prev_paragraph()


class ClauseSequenceControls:
    def __init__(self):
        pass

    def get_component(self):
        pass

    def update_display(self):
        pass

    def next_sequence(self, event):
        pass

    def prev_sequence(self, event):
        pass

    def add_sequence(self, event):
        pass

    def delete_sequence(self, event):
        pass


class Controls:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller
        self.paragraph_controls = ParagraphControls(self.controller)
        self.clause_sequence_controls = ClauseSequenceControls()

        self.component = Column(
            self.paragraph_controls.get_component(),
            self.clause_sequence_controls.get_component(),
            styles=controls_style,
            sizing_mode="stretch_width"
        )

    def update_display(self):
        self.paragraph_controls.update_display()
        self.clause_sequence_controls.update_display()

    def get_component(self):
        return self.component
