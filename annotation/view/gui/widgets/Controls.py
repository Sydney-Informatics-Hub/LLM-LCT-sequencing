from typing import Optional, Callable

import panel as pn
from panel import Row, Column, bind
from panel.widgets import Button, RadioButtonGroup, CrossSelector
from panel.pane import Str, HTML

from annotation.controller.AnnotationController import AnnotationController
from .styles import (controls_style, sequence_heading_style, delete_sequence_button_style, add_sequence_button_style,
                     clause_stylesheet, sequence_info_style, classification_heading_style, sequence_classification_style,
                     classification_subheading_style, llm_class_display_style, manage_sequence_button_style)


class ClauseSequenceControls:
    def __init__(self, controller: AnnotationController, add_sequence_controls_fn: Callable):
        self.controller: AnnotationController = controller
        self.add_sequence_controls_fn = add_sequence_controls_fn

        self.title = Str("Clause Pair Sequence", styles=sequence_heading_style)
        self.clause_a_info = HTML(ClauseSequenceControls.format_first_clause_str(), stylesheets=[clause_stylesheet])
        self.clause_overlap_info = HTML(ClauseSequenceControls.format_overlap_str(), stylesheets=[clause_stylesheet])
        self.clause_b_info = HTML(ClauseSequenceControls.format_second_clause_str(), stylesheets=[clause_stylesheet])
        self.prev_sequence_button = Button(name="\N{LEFTWARDS ARROW TO BAR} PREV", button_type="primary",
                                           button_style="outline")
        self.next_sequence_button = Button(name="NEXT \N{RIGHTWARDS ARROW TO BAR}", button_type="primary",
                                           button_style="outline")
        self.manage_sequence_button = Button(name="Manage sequence", button_type="primary", button_style="outline", styles=manage_sequence_button_style)
        self.delete_sequence_button = Button(name="Delete", button_type="danger", styles=delete_sequence_button_style)
        self.add_sequence_button = Button(name="Add", button_type="success", styles=add_sequence_button_style)

        self.prev_sequence_button.on_click(self.prev_sequence)
        self.next_sequence_button.on_click(self.next_sequence)
        self.manage_sequence_button.on_click(self.toggle_show_manage_sequence_pane)
        self.delete_sequence_button.on_click(self.delete_sequence)
        self.add_sequence_button.on_click(self.show_add_sequence_pane)

        self.component = Column(
            Row(self.title,
                align="center"),
            Row(
                self.prev_sequence_button,
                Column(
                    self.clause_a_info,
                    self.clause_b_info,
                    self.clause_overlap_info,
                    styles=sequence_info_style
                ),
                self.next_sequence_button
            ),
            Row(
                Column(
                    Row(
                        self.manage_sequence_button,
                        align="center"
                    ),
                    Row(
                        self.delete_sequence_button,
                        self.add_sequence_button,
                        align="center"
                    )
                ),
                align="center"
            ),
            align="center"
        )

    @staticmethod
    def format_first_clause_str(clause_range: Optional[tuple[int, int]] = None) -> str:
        clause_str: str = f"<span class=\"first_clause\"><strong>Clause A:</strong> "
        if clause_range is not None:
            clause_str += f"{clause_range[0]} - {clause_range[1]}"
        clause_str += "</span>"

        return clause_str

    @staticmethod
    def format_second_clause_str(clause_range: Optional[tuple[int, int]] = None) -> str:
        clause_str: str = f"<span class=\"second_clause\"><strong>Clause B:</strong> "
        if clause_range is not None:
            clause_str += f"{clause_range[0]} - {clause_range[1]}"
        clause_str += "</span>"

        return clause_str

    @staticmethod
    def format_overlap_str(overlap_range: Optional[tuple[int, int]] = None) -> str:
        if overlap_range is None:
            # Returning a space character is necessary because the HTML pane does not register the change in text if
            # the string is empty
            return " "

        return f"<span class=\"clause_overlap\"><strong>Overlap:</strong> {overlap_range[0]} - {overlap_range[1]}</span>"

    @staticmethod
    def get_clause_overlap(clause_a_range: tuple[int, int], clause_b_range: tuple[int, int]) -> Optional[tuple[int, int]]:
        if (clause_a_range is None) or (clause_b_range is None):
            return
        if (clause_a_range[0] <= clause_b_range[0]) and (clause_b_range[0] <= clause_a_range[1]):
            return clause_b_range[0], clause_a_range[1]
        elif (clause_b_range[0] <= clause_a_range[0]) and (clause_a_range[0] <= clause_b_range[1]):
            return clause_a_range[0], clause_b_range[1]

    def get_component(self):
        return self.component

    def set_visibility(self, is_visible: bool):
        self.component.visible = is_visible

    def toggle_visibility(self):
        self.component.visible = not self.component.visible

    def update_display(self):
        clause_ranges = self.controller.get_curr_sequence()
        if clause_ranges is None:
            clause_a_range, clause_b_range = None, None
        else:
            clause_a_range, clause_b_range = clause_ranges
        self.clause_a_info.object = ClauseSequenceControls.format_first_clause_str(clause_a_range)
        self.clause_b_info.object = ClauseSequenceControls.format_second_clause_str(clause_b_range)
        overlap_range = ClauseSequenceControls.get_clause_overlap(clause_a_range, clause_b_range)
        self.clause_overlap_info.object = ClauseSequenceControls.format_overlap_str(overlap_range)
        self.reset_manage_sequence_pane()

    def next_sequence(self, event):
        self.controller.next_sequence()

    def prev_sequence(self, event):
        self.controller.prev_sequence()

    def toggle_show_manage_sequence_pane(self, event):
        manage_button_style = self.manage_sequence_button.button_style
        if manage_button_style == "outline":
            self.manage_sequence_button.button_style = "solid"
        elif manage_button_style == "solid":
            self.manage_sequence_button.button_style = "outline"

        self.delete_sequence_button.visible = not self.delete_sequence_button.visible
        self.add_sequence_button.visible = not self.add_sequence_button.visible

    def reset_manage_sequence_pane(self):
        self.manage_sequence_button.button_style = "outline"
        self.delete_sequence_button.visible = False
        self.add_sequence_button.visible = False

    def show_add_sequence_pane(self, event):
        self.add_sequence_controls_fn()

    def delete_sequence(self, event):
        self.controller.delete_curr_sequence()


class AddSequenceControls:
    def __init__(self, controller: AnnotationController, reset_visibility_fn: Callable):
        self.controller: AnnotationController = controller
        self.reset_visibility_fn = reset_visibility_fn

        self.back_button = Button(name="Back", button_type="danger", button_style="outline")
        self.clause_selector = CrossSelector(name="Clauses", definition_order=False)
        self.save_sequence_button = Button(name="Save", button_type="success", button_style="outline")

        self.back_button.on_click(self.exit_pane)
        self.save_sequence_button.on_click(self.save_sequence)

        self.component = Column(
            self.clause_selector,
            self.back_button,
            self.save_sequence_button,
            align="center"
        )

    def get_component(self):
        return self.component

    def update_display(self):
        if not self.component.visible:
            return

        clause_selector_options = {}
        for clause_data in self.controller.get_clauses():
            clause_id = clause_data[0]
            clause_text = clause_data[1]
            clause_selector_options[clause_text] = clause_id

        self.clause_selector.options = clause_selector_options

    def set_visibility(self, is_visible: bool):
        self.component.visible = is_visible

    def toggle_visibility(self):
        self.component.visible = not self.component.visible

    def save_sequence(self, event):
        selections: list[int] = self.clause_selector.value
        if len(selections) != 2:
            pn.state.notifications.error('A clause sequence must contain exactly 2 clauses. '
                                         'Please select 2 clauses in the clause selector', duration=5000)
            return

        new_id: int = self.controller.add_sequence(int(selections[0]), int(selections[1]))
        if new_id == -1:
            pn.state.notifications.error('Clause sequence already exists', duration=5000)
            return
        else:
            self.exit_pane()

    def exit_pane(self, event=None):
        self.clause_selector.value = []
        self.clause_selector.options = []
        self.reset_visibility_fn()


class SequenceClassificationControls:
    UNSELECTED: str = "No change"

    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller

        self.title = Str("Sequence Classification", styles=classification_heading_style)
        self.llm_class_title = Str("LLM", styles=classification_subheading_style)
        self.llm_class_display = Str("", styles=llm_class_display_style)
        self.user_class_title = Str("User", styles=classification_subheading_style)
        classification_options = [SequenceClassificationControls.UNSELECTED] + self.controller.get_all_classifications()
        self.classification_selector = RadioButtonGroup(
            name="Sequence Classifications",
            options=classification_options,
            button_type="primary", button_style="outline"
        )
        selector_bound_fn = bind(self.set_correct_classification, classification=self.classification_selector)

        self.component = Column(
            Row(self.title,
                align="center"),
            Row(self.llm_class_title,
                align="center"),
            Row(self.llm_class_display,
                align="center"),
            Row(self.user_class_title,
                align="center"),
            Row(self.classification_selector,
                align="center"),
            Row(selector_bound_fn, visible=False),
            styles=sequence_classification_style,
            align="center"
        )

    def get_component(self):
        return self.component

    def set_visibility(self, is_visible: bool):
        self.component.visible = is_visible

    def toggle_visibility(self):
        self.component.visible = not self.component.visible

    def update_display(self):
        curr_correct_class = self.controller.get_correct_classification()
        if curr_correct_class not in self.controller.get_all_classifications():
            curr_correct_class = SequenceClassificationControls.UNSELECTED
        self.classification_selector.value = curr_correct_class
        self.llm_class_display.object = self.controller.get_predicted_classification()

    def set_correct_classification(self, classification):
        self.controller.set_correct_classification(classification)


class Controls:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller
        self.clause_sequence_controls = ClauseSequenceControls(self.controller, self.add_sequence_controls)
        self.sequence_classification_controls = SequenceClassificationControls(self.controller)
        self.add_sequence_controls = AddSequenceControls(self.controller, self.reset_visibility)

        self.component = Column(
            self.clause_sequence_controls.get_component(),
            self.sequence_classification_controls.get_component(),
            self.add_sequence_controls.get_component(),
            styles=controls_style,
            sizing_mode="stretch_width"
        )

        self.reset_visibility()

        self.controller.add_update_text_display_callable(self.update_display)

    def update_display(self):
        self.clause_sequence_controls.update_display()
        self.sequence_classification_controls.update_display()
        self.add_sequence_controls.update_display()

    def get_component(self):
        return self.component

    def add_sequence_controls(self):
        self.add_sequence_controls.set_visibility(True)
        self.clause_sequence_controls.set_visibility(False)
        self.sequence_classification_controls.set_visibility(False)

        self.update_display()

    def reset_visibility(self):
        self.add_sequence_controls.set_visibility(False)
        self.clause_sequence_controls.set_visibility(True)
        self.sequence_classification_controls.set_visibility(True)

        self.update_display()