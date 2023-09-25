import panel as pn
from panel import Column

from .styles import curr_paragraph_style, context_paragraph_style, FIRST_CLAUSE_COLOUR, \
    SECOND_CLAUSE_COLOUR, OVERLAP_COLOUR, text_display_style


class ContextParagraph:
    """
    Defines a paragraph of text and its associated styling.
    The styling defined will be applied uniformly to the text when get_styled_paragraph() is called
    """

    def __init__(self, text: str = ""):
        self.text: str = text
        self.styles: dict[str, str] = context_paragraph_style

    def get_styled_pane(self) -> pn.pane.PaneBase:
        return pn.pane.HTML(
            self.text,
            styles=self.styles
        )


class CurrentParagraph:
    """
    Defines a paragraph of text, its associated styling, and up to two clauses to be highlighted with custom colours.
    clause_a_range and clause_b_range can be set using the setters. The ranges specified are inclusive
    """

    def __init__(self, text: str = ""):
        self.text: str = text
        self.styles: dict[str, str] = curr_paragraph_style
        self.clause_a_range: list[int, int] | None = None
        self.clause_b_range: list[int, int] | None = None

    def do_clauses_overlap(self) -> bool:
        """
        Returns True if both clauses are not None and have overlapping ranges, False otherwise
        """
        if (self.clause_a_range is None) or (self.clause_b_range is None):
            return False

        a_start, a_end = self.clause_a_range
        b_start, b_end = self.clause_b_range

        return ((a_start <= b_start) and (b_start <= a_end)) or ((b_start <= a_start) and (a_start <= b_end))

    def get_styled_pane(self) -> pn.pane.PaneBase:
        """
        Inserts HTML span tags around the clauses in the paragraph and returns a rendered HTML pane, applying the custom styling to the clauses
        If the two clauses overlap, a third set of span tags will surround the overlapped section.
        Returns a rendered HTML pane
        """
        to_render: str
        if (self.clause_a_range is None) and (self.clause_b_range is None):
            to_render = self.text
        else:
            # Both clauses exist but order is not yet determined
            if self.clause_a_range[0] <= self.clause_b_range[0]:
                first_clause_range = self.clause_a_range.copy()
                second_clause_range = self.clause_b_range.copy()
            else:
                first_clause_range = self.clause_b_range.copy()
                second_clause_range = self.clause_a_range.copy()

            if self.do_clauses_overlap():
                # If clauses overlap, a set of span tags will be inserted around the overlap and the clause ranges will be adjusted accordingly
                overlap_range = [second_clause_range[0], first_clause_range[1]]
                first_clause_range[1] = overlap_range[0] - 1
                second_clause_range[0] = overlap_range[1] + 1

                first_clause_text = self.text[first_clause_range[0]:first_clause_range[1] + 1]
                first_clause_render = f"<span style=\"background-color:{FIRST_CLAUSE_COLOUR}\">{first_clause_text}</span>"
                second_clause_text = self.text[second_clause_range[0]:second_clause_range[1] + 1]
                second_clause_render = f"<span style=\"background-color:{SECOND_CLAUSE_COLOUR}\">{second_clause_text}</span>"
                overlap_text = self.text[overlap_range[0]:overlap_range[1] + 1]
                overlap_render = f"<span style=\"background-color:{OVERLAP_COLOUR}\">{overlap_text}</span>"

                to_render = ""
                if overlap_range[0] > 0:
                    # If both clauses begin at the start of the text, the first clause can be omitted from the render
                    to_render += self.text[:first_clause_range[0]] + first_clause_render
                to_render += overlap_render
                if overlap_range[1] < (len(self.text) - 1):
                    # If both clauses end at the end of the text, the second clause can be omitted from the render
                    to_render += second_clause_render + self.text[second_clause_range[1] + 1:]
            else:
                first_clause_text = self.text[first_clause_range[0]:first_clause_range[1] + 1]
                first_clause_render = f"<span style=\"background-color:{FIRST_CLAUSE_COLOUR}\">{first_clause_text}</span>"
                second_clause_text = self.text[second_clause_range[0]:second_clause_range[1] + 1]
                second_clause_render = f"<span style=\"background-color:{SECOND_CLAUSE_COLOUR}\">{second_clause_text}</span>"

                to_render = (self.text[:first_clause_range[0]] + first_clause_render +
                             self.text[first_clause_range[1] + 1:second_clause_range[0]] +
                             second_clause_render + self.text[second_clause_range[1] + 1:])

        return pn.pane.HTML(
            to_render,
            styles=self.styles
        )

    def set_clause_a_range(self, clause_a_range: list[int, int] | None):
        """
        Sets the character index range for Clause A.
        The range defined is inclusive. The second integer must be greater than the first.
        Parameters
        ----------
        clause_a_range: list[int, int] - The start and end index of range defined for Clause A
        """
        if clause_a_range is None:
            self.clause_a_range = clause_a_range
            return
        if type(clause_a_range) is not list:
            raise TypeError("clause_a_range must be a list")
        if (type(clause_a_range[0]) is not int) or (type(clause_a_range[1]) is not int):
            raise TypeError("clause_a_range must only contain integers")

        if clause_a_range[1] <= clause_a_range[0]:
            raise ValueError("The second integer of clause_a_range must be greater than the second integer")

        self.clause_a_range = clause_a_range.copy()

    def set_clause_b_range(self, clause_b_range: list[int, int] | None):
        """
        Sets the character index range for Clause B.
        The range defined is inclusive. The second integer must be greater than the first.
        Parameters
        ----------
        clause_b_range: list[int, int] - The start and end index of range defined for Clause B
        """
        if clause_b_range is None:
            self.clause_a_range = clause_b_range
            return
        if type(clause_b_range) is not list:
            raise TypeError("clause_b_range must be a list")
        if (type(clause_b_range[0]) is not int) or (type(clause_b_range[1]) is not int):
            raise TypeError("clause_b_range must only contain integers")

        if clause_b_range[1] <= clause_b_range[0]:
            raise ValueError("The second integer of clause_b_range must be greater than the second integer")

        self.clause_b_range = clause_b_range.copy()


class TextDisplay:
    """
    Controls the text view and rendering
    """
    def __init__(self):
        self.prev_paragraph = ContextParagraph()
        self.curr_paragraph = CurrentParagraph()
        self.next_paragraph = ContextParagraph()

    def get_widget(self):
        return Column(
            self.prev_paragraph.get_styled_pane(),
            self.curr_paragraph.get_styled_pane(),
            self.next_paragraph.get_styled_pane(),
            styles=text_display_style,
            sizing_mode="stretch_width"
        )

    def set_curr_paragraph(self, text: str):
        self.curr_paragraph = CurrentParagraph(text)

    def set_clause_a_range(self, clause_a_range: list[int, int] | None):
        """
        Calls the method of the same name on the current paragraph object (unless curr_paragraph is None)
        """
        if self.curr_paragraph is not None:
            self.curr_paragraph.set_clause_a_range(clause_a_range)

    def set_clause_b_range(self, clause_b_range: list[int, int] | None):
        """
        Calls the method of the same name on the current paragraph object (unless curr_paragraph is None)
        """
        if self.curr_paragraph is not None:
            self.curr_paragraph.set_clause_b_range(clause_b_range)

    def set_prev_paragraph(self, text: str):
        self.prev_paragraph = ContextParagraph(text)

    def set_next_paragraph(self, text: str):
        self.next_paragraph = ContextParagraph(text)
