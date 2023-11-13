import re
from typing import Optional

from panel import Column
from panel.pane import HTML

from annotation.controller.AnnotationController import AnnotationController
from .styles import text_display_style, clause_stylesheet


class TextRender:
    """
    Defines text and up to two clauses to be highlighted with custom colours.
    clause_a_range and clause_b_range can be set using the setters. The ranges specified are inclusive
    """
    def __init__(self, text: str = ""):
        self.raw_text: str = text

        self.clause_a_range: Optional[tuple[int, int]] = None
        self.clause_b_range: Optional[tuple[int, int]] = None
        self.linkage_word_ranges: list[tuple[int, int]] = []

    def set_text(self, text: str):
        if type(text) is not str:
            raise TypeError(f"text must be str, but got {type(text)}")
        self.raw_text = text

    def do_clauses_overlap(self) -> bool:
        """
        Returns True if both clauses are not None and have overlapping ranges, False otherwise
        """
        if (self.clause_a_range is None) or (self.clause_b_range is None):
            return False

        a_start, a_end = self.clause_a_range
        b_start, b_end = self.clause_b_range

        return ((a_start <= b_start) and (b_start < a_end)) or ((b_start <= a_start) and (a_start < b_end))

    def _repr_html_(self) -> str:
        text_ls: list[str] = list(self.raw_text)
        # Append an empty string to allow for the closing span tag at the end of the text
        text_ls.append('')

        for i, char in enumerate(text_ls):
            # Replace file newline characters with HTML newlines
            if (char == "\n") or (char == "\r\n"):
                text_ls[i] = "<br>"

        for linkage_word_range in self.linkage_word_ranges:
            text_ls[linkage_word_range[0]] = "<span class=\"linkage_word\">" + text_ls[linkage_word_range[0]]
            text_ls[linkage_word_range[1]-1] = text_ls[linkage_word_range[1]-1] + "</span>"

        clauses_overlap: bool = self.do_clauses_overlap()
        if clauses_overlap:
            overlap_range = [self.clause_b_range[0], self.clause_a_range[1]]

            text_ls[self.clause_a_range[0]] = "<span class=\"first_clause\">" + text_ls[self.clause_a_range[0]]
            text_ls[overlap_range[0]] = "</span><span class=\"clause_overlap\">" + text_ls[overlap_range[0]]
            text_ls[overlap_range[1]] = "</span><span class=\"second_clause\">" + text_ls[overlap_range[1]]
            text_ls[self.clause_b_range[1]] = "</span>" + text_ls[self.clause_b_range[1]]
        else:
            if self.clause_a_range is not None:
                text_ls[self.clause_a_range[0]] = "<span class=\"first_clause\">" + text_ls[self.clause_a_range[0]]
            if self.clause_b_range is not None:
                text_ls[self.clause_b_range[0]] = "<span class=\"second_clause\">" + text_ls[self.clause_b_range[0]]
                text_ls[self.clause_b_range[1]] = "</span>" + text_ls[self.clause_b_range[1]]
            if self.clause_a_range is not None:
                text_ls[self.clause_a_range[1]] = "</span>" + text_ls[self.clause_a_range[1]]

        window_start: int = 0
        window_end: int = -1
        if self.clause_a_range is not None:
            window_start = self.clause_a_range[0]
        if self.clause_b_range is not None:
            window_end = self.clause_b_range[1]

        html_text: str = "".join(text_ls[window_start:window_end])

        return html_text

    def set_clause_a_range(self, clause_a_range: Optional[tuple[int, int]]):
        """
        Sets the character index range for Clause A.
        The range defined is inclusive. The second integer must be greater than the first.
        Parameters
        ----------
        clause_a_range: tuple[int, int] - The start and end index of range defined for Clause A
        """
        if clause_a_range is None:
            self.clause_a_range = clause_a_range
            return
        if type(clause_a_range) is not tuple:
            raise TypeError(f"clause_a_range: expected type tuple, provided type {type(clause_a_range)}")
        if len(clause_a_range) != 2:
            raise ValueError("clause_a_range must contain exactly two elements")
        if (type(clause_a_range[0]) is not int) or (type(clause_a_range[1]) is not int):
            raise TypeError("clause_a_range must only contain integers")
        if clause_a_range[1] <= clause_a_range[0]:
            raise ValueError(f"The second integer of clause_a_range (provided: {clause_a_range[1]}) "
                             f"must be greater than the first integer (provided: {clause_a_range[0]})")

        self.clause_a_range = clause_a_range

    def set_clause_b_range(self, clause_b_range: Optional[tuple[int, int]]):
        """
        Sets the character index range for Clause B.
        The range defined is inclusive. The second integer must be greater than the first.
        Parameters
        ----------
        clause_b_range: tuple[int, int] - The start and end index of range defined for Clause B
        """
        if clause_b_range is None:
            self.clause_b_range = clause_b_range
            return
        if type(clause_b_range) is not tuple:
            raise TypeError("clause_b_range must be a tuple")
        if len(clause_b_range) != 2:
            raise ValueError("clause_b_range must contain exactly two elements")
        if (type(clause_b_range[0]) is not int) or (type(clause_b_range[1]) is not int):
            raise TypeError("clause_b_range must only contain integers")
        if clause_b_range[1] <= clause_b_range[0]:
            raise ValueError(f"The second integer of clause_b_range (provided: {clause_b_range[1]}) "
                             f"must be greater than the first integer (provided: {clause_b_range[0]})")

        self.clause_b_range = clause_b_range

    def update_linkage_word_ranges(self, linkage_words: list[str]):
        """
        Iterates over the provided list of strings, identifies their occurrences within the current clauses,
        and sets the linkage_word ranges to the corresponding indexes of the occurrences.
        Parameters
        ----------
        linkage_words: Optional[list[str]] - A list of linkage words that occur within the currently set clauses.
        If None or empty, the linkage words will be set to an empty list
        """
        if linkage_words is None:
            self.linkage_word_ranges = []
            return
        if len(linkage_words) == 0:
            self.linkage_word_ranges = []
            return

        linkage_word_ranges: list[tuple[int, int]] = []

        for linkage_word in linkage_words:
            # pattern = r'\b' + re.escape(linkage_word) + r'\b'
            pattern = re.escape(linkage_word)

            for clause_range in [self.clause_a_range, self.clause_b_range]:
                if clause_range is not None:
                    clause_text = self.raw_text[clause_range[0]:clause_range[1]]
                    clause_match = re.finditer(pattern, clause_text)
                    for match in clause_match:
                        base_idx = clause_range[0]
                        new_range: tuple = (base_idx + match.start()), (base_idx + match.end())
                        linkage_word_ranges.append(new_range)

        self.linkage_word_ranges = linkage_word_ranges


class TextDisplay:
    """
    Controls the text view and rendering
    """
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller
        self.text_render: TextRender = TextRender(self.controller.get_text())
        self.text_html = HTML(self.text_render, stylesheets=[clause_stylesheet])
        self.component = Column(self.text_html,
                                scroll=True,
                                styles=text_display_style,
                                sizing_mode="stretch_width")

        self.controller.add_update_text_display_callable(self.update_display)

    def update_display(self):
        clause_ranges = self.controller.get_curr_sequence_ranges()
        if clause_ranges is None:
            clause_a_range, clause_b_range = None, None
        else:
            clause_a_range, clause_b_range = clause_ranges
        self.text_render.set_clause_a_range(clause_a_range)
        self.text_render.set_clause_b_range(clause_b_range)
        linkage_words: Optional[list[str]] = self.controller.get_curr_sequence_linkage_words()
        self.text_render.update_linkage_word_ranges(linkage_words)

        self.set_text(self.controller.get_text())

    def get_component(self):
        return self.component

    def set_text(self, text: str):
        self.text_render.set_text(text)
        self.text_html.object = self.text_render
