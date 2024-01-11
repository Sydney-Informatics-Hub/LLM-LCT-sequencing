from typing import Optional, Callable

from panel import Row, Column, bind
from panel.layout import Divider
from panel.widgets import Button, CheckButtonGroup, FileDownload, MultiSelect
from panel.pane import Str, HTML, Markdown

from annotation.controller.AnnotationController import AnnotationController
from .styles import (controls_style, sequence_heading_style, delete_sequence_button_style, add_sequence_button_style,
                     clause_stylesheet, sequence_info_style, classification_heading_style,
                     sequence_classification_style, manage_sequence_button_style)


class ClauseSequenceControls:
    def __init__(self, controller: AnnotationController, add_sequence_controls_fn: Callable):
        self.controller: AnnotationController = controller
        self.add_sequence_controls_fn = add_sequence_controls_fn

        self.title = Str("Clause Pair Sequence", styles=sequence_heading_style)
        self.clause_a_info = HTML(ClauseSequenceControls.format_first_clause_str(), stylesheets=[clause_stylesheet])
        self.clause_b_info = HTML(ClauseSequenceControls.format_second_clause_str(), stylesheets=[clause_stylesheet])
        self.clause_overlap_info = HTML(ClauseSequenceControls.format_overlap_str(), stylesheets=[clause_stylesheet])
        self.linkage_word_info = HTML(ClauseSequenceControls.format_linkage_str(), stylesheets=[clause_stylesheet])
        self.prev_sequence_button = Button(name="\N{LEFTWARDS ARROW TO BAR} PREV", button_type="primary",
                                           button_style="outline")
        self.next_sequence_button = Button(name="NEXT \N{RIGHTWARDS ARROW TO BAR}", button_type="primary",
                                           button_style="outline")
        self.manage_sequence_button = Button(name="Manage sequence", button_type="primary", button_style="outline",
                                             styles=manage_sequence_button_style)
        self.delete_sequence_button = Button(name="Delete sequence", button_type="danger", styles=delete_sequence_button_style)
        self.add_sequence_button = Button(name="Add sequence", button_type="success", styles=add_sequence_button_style)

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
                    self.linkage_word_info,
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
    def format_linkage_str(linkage_words: Optional[list[str]] = None) -> str:
        linkage_str: str = f"<span class=\"linkage_word\"><strong>Linkage words:</strong> "
        if linkage_words is not None:
            linkage_str += ", ".join(linkage_words)
        linkage_str += "</span>"

        return linkage_str

    @staticmethod
    def get_clause_overlap(clause_a_range: tuple[int, int], clause_b_range: tuple[int, int]) -> Optional[tuple[int, int]]:
        if (clause_a_range is None) or (clause_b_range is None):
            return

        a_start, a_end = clause_a_range
        b_start, b_end = clause_b_range

        overlap_start = max(a_start, b_start)
        overlap_end = min(a_end, b_end)

        if overlap_start < overlap_end:
            return overlap_start, overlap_end

    def get_component(self):
        return self.component

    def set_visibility(self, is_visible: bool):
        self.component.visible = is_visible

    def toggle_visibility(self):
        self.component.visible = not self.component.visible

    def update_display(self):
        clause_ranges = self.controller.get_curr_sequence_ranges()
        if clause_ranges is None:
            clause_a_range, clause_b_range = None, None
        else:
            clause_a_range, clause_b_range = clause_ranges
        self.clause_a_info.object = ClauseSequenceControls.format_first_clause_str(clause_a_range)
        self.clause_b_info.object = ClauseSequenceControls.format_second_clause_str(clause_b_range)
        overlap_range = ClauseSequenceControls.get_clause_overlap(clause_a_range, clause_b_range)
        self.clause_overlap_info.object = ClauseSequenceControls.format_overlap_str(overlap_range)
        linkage_words: Optional[list[str]] = self.controller.get_curr_sequence_linkage_words()
        self.linkage_word_info.object = ClauseSequenceControls.format_linkage_str(linkage_words)

        self.reset_manage_sequence_pane()

    def next_sequence(self, event):
        self.controller.next_sequence()

    def prev_sequence(self, event):
        self.controller.prev_sequence()

    def toggle_show_manage_sequence_pane(self, *_):
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

    def show_add_sequence_pane(self, *_):
        self.add_sequence_controls_fn()

    def delete_sequence(self, event):
        self.controller.delete_curr_sequence()


class AddSequenceControls:
    def __init__(self, controller: AnnotationController, reset_visibility_fn: Callable):
        self.controller: AnnotationController = controller
        self.reset_visibility_fn = reset_visibility_fn

        self.clause_selector = MultiSelect(name="Clauses", size=10, width=600)
        self.back_button = Button(name="Back", button_type="danger", button_style="outline")
        self.save_sequence_button = Button(name="Save", button_type="success", button_style="outline")

        self.back_button.on_click(self.exit_pane)
        self.save_sequence_button.on_click(self.save_sequence)

        self.component = Column(
            self.clause_selector,
            Row(self.back_button,
                self.save_sequence_button
                ),
            align="center"
        )

    def get_component(self):
        return self.component

    def update_display(self):
        if not self.component.visible:
            return

        clause_selector_options = {}
        for clause_id, clause_text in self.controller.get_all_clause_text().items():
            unique_clause_text = f"{clause_id}-{clause_text}"
            clause_selector_options[unique_clause_text] = clause_id

        self.clause_selector.options = clause_selector_options

    def set_visibility(self, is_visible: bool):
        self.component.visible = is_visible

    def toggle_visibility(self):
        self.component.visible = not self.component.visible

    def save_sequence(self, *_):
        selections: list[int] = self.clause_selector.value
        if len(selections) != 2:
            self.controller.display_error('A clause sequence must contain exactly 2 clauses. '
                                          'Please select 2 clauses in the clause selector')
            return

        new_id: int = self.controller.add_sequence(int(selections[0]), int(selections[1]))
        if new_id == -1:
            self.controller.display_error('Clause sequence already exists')
            return
        else:
            self.exit_pane()

    def exit_pane(self, *_):
        self.clause_selector.value = []
        self.clause_selector.options = []
        self.reset_visibility_fn()


class SequenceClassificationControls:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller

        self.title = Str("Sequence Classification", styles=classification_heading_style)
        self.revert_to_llm_button = Button(name="Revert to prediction", disabled=True,
                                           button_type="primary", button_style="outline")
        self.revert_to_llm_button.on_click(self.revert_to_prediction)
        self.llm_reasoning_display = Markdown("**LLM Reasoning:**", sizing_mode="stretch_width", height_policy="fit", visible=False)
        classification_options = self.controller.get_all_classifications()
        # The first option is 'NA', which does not need to be displayed
        self.no_classification_text = classification_options[0]
        classification_options = classification_options[1:]
        self.classification_selector = CheckButtonGroup(
            name="Sequence Classifications",
            options=classification_options,
            value=[],
            button_type="primary", button_style="outline"
        )
        selector_bound_fn = bind(self.set_correct_classification, classifications=self.classification_selector)

        self.component = Column(
            Row(self.title,
                align="center"),
            Row(self.revert_to_llm_button,
                align="center"),
            Row(self.classification_selector,
                align="center"),
            Row(self.llm_reasoning_display,
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
        curr_correct_classes: list[str] = self.controller.get_correct_classifications()
        if len(curr_correct_classes) == 0:
            curr_correct_classes = self.controller.get_predicted_classifications()
        self.classification_selector.value = curr_correct_classes
        reasoning: str = self.controller.get_reasoning()
        if reasoning == '':
            self.llm_reasoning_display.object = '**LLM Reasoning:**'
            self.llm_reasoning_display.visible = False
        else:
            self.llm_reasoning_display.object = '**LLM Reasoning:** ' + reasoning
            self.llm_reasoning_display.visible = True

    def revert_to_prediction(self, *_):
        self.classification_selector.value = self.controller.get_predicted_classifications()
        self.revert_to_llm_button.disabled = True
        self.revert_to_llm_button.button_style = "outline"

    def set_correct_classification(self, classifications: list[str]):
        predicted_classes: list[str] = self.controller.get_predicted_classifications()
        if predicted_classes == classifications:
            self.revert_to_llm_button.disabled = True
            self.revert_to_llm_button.button_style = "outline"
        else:
            self.revert_to_llm_button.disabled = False
            self.revert_to_llm_button.button_style = "solid"

        if len(classifications) == 0:
            self.controller.set_correct_classifications([self.no_classification_text])
        else:
            self.controller.set_correct_classifications(self.classification_selector.value)


class ExportControls:
    FILENAME: str = "sequence_annotation"

    def __init__(self, controller: AnnotationController, reset_visibility_fn: Callable):
        self.controller: AnnotationController = controller
        self.reset_visibility_fn = reset_visibility_fn

        self.show_options_button = Button(name="Show export options", button_type="success", button_style="outline")
        file_download_buttons = [FileDownload(
            label=f"Export to {ftype}",
            filename=f"{ExportControls.FILENAME}.{ftype}",
            callback=bind(self.export, filetype=ftype),
            button_type="primary",
            button_style="outline") for ftype in self.controller.get_export_file_formats()]
        self.export_buttons = Row(
            *file_download_buttons,
            visible=False
        )

        self.show_options_button.on_click(self.toggle_options_visibility)

        self.component = Column(
            self.show_options_button,
            self.export_buttons,
            align="start"
        )

    def get_component(self):
        return self.component

    def set_visibility(self, is_visible: bool):
        self.component.visible = is_visible

    def toggle_visibility(self):
        self.component.visible = not self.component.visible

    def export(self, filetype: str, *_):
        return self.controller.export(filetype)

    def toggle_options_visibility(self, *_):
        self.export_buttons.visible = not self.export_buttons.visible
        if self.export_buttons.visible:
            self.show_options_button.name = "Hide export options"
            self.show_options_button.button_style = "solid"
        else:
            self.show_options_button.name = "Show export options"
            self.show_options_button.button_style = "outline"


class Controls:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller
        self.clause_sequence_controls = ClauseSequenceControls(self.controller, self.add_sequence_controls)
        self.sequence_classification_controls = SequenceClassificationControls(self.controller)
        self.add_sequence_controls = AddSequenceControls(self.controller, self.reset_visibility)
        self.export_controls = ExportControls(self.controller, self.reset_visibility)

        self.component = Column(
            self.clause_sequence_controls.get_component(),
            self.sequence_classification_controls.get_component(),
            self.add_sequence_controls.get_component(),
            Divider(),
            self.export_controls.get_component(),
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
        self.export_controls.set_visibility(True)

        self.update_display()
