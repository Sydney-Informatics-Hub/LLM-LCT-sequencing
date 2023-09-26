import panel as pn
from panel import Column
from panel.pane import HTML

from .styles import curr_paragraph_style, context_paragraph_style, text_display_style, clause_stylesheet


class ContextParagraph:
    """
    Defines a paragraph of text
    """

    def __init__(self, text: str = ""):
        self.text: str = text

    def set_text(self, text: str):
        if type(text) is not str:
            raise TypeError("text must be str")
        self.text = text

    def _repr_html_(self) -> str:
        return self.text


class CurrentParagraph:
    """
    Defines a paragraph of text and up to two clauses to be highlighted with custom colours.
    clause_a_range and clause_b_range can be set using the setters. The ranges specified are inclusive
    """

    def __init__(self, text: str = ""):
        self.raw_text: str = text

        self.clause_a_range: tuple[int, int] | None = None
        self.clause_b_range: tuple[int, int] | None = None

    def set_text(self, text: str):
        if type(text) is not str:
            raise TypeError("text must be str")
        self.raw_text = text

    def do_clauses_overlap(self) -> bool:
        """
        Returns True if both clauses are not None and have overlapping ranges, False otherwise
        """
        if (self.clause_a_range is None) or (self.clause_b_range is None):
            return False

        a_start, a_end = self.clause_a_range
        b_start, b_end = self.clause_b_range

        return ((a_start <= b_start) and (b_start <= a_end)) or ((b_start <= a_start) and (a_start <= b_end))

    def _repr_html_(self) -> str:
        """
        Inserts HTML span tags around the clauses in the paragraph and returns the HTML string.
        If the two clauses overlap, a third set of span tags will surround the overlapped section.
        """
        html_text: str
        if (self.clause_a_range is None) or (self.clause_b_range is None):
            # If one or both of the clauses are not present, then no html tags need to be inserted
            return self.raw_text

        # Both clauses exist but order is not yet determined
        if self.clause_a_range[0] <= self.clause_b_range[0]:
            first_clause_range = list(self.clause_a_range)
            second_clause_range = list(self.clause_b_range)
        else:
            first_clause_range = list(self.clause_b_range)
            second_clause_range = list(self.clause_a_range)

        if self.do_clauses_overlap():
            # If clauses overlap, a set of span tags will be inserted around the overlap and the clause ranges will be adjusted accordingly
            overlap_range = [second_clause_range[0], first_clause_range[1]]
            first_clause_range[1] = overlap_range[0] - 1
            second_clause_range[0] = overlap_range[1] + 1

            first_clause_text = self.raw_text[first_clause_range[0]:first_clause_range[1] + 1]
            first_clause_render = f"<span class=\"first_clause\">{first_clause_text}</span>"
            second_clause_text = self.raw_text[second_clause_range[0]:second_clause_range[1] + 1]
            second_clause_render = f"<span class=\"second_clause\">{second_clause_text}</span>"
            overlap_text = self.raw_text[overlap_range[0]:overlap_range[1] + 1]
            overlap_render = f"<span class=\"clause_overlap\">{overlap_text}</span>"

            html_text = ""
            if overlap_range[0] > 0:
                # If both clauses begin at the start of the text, the first clause can be omitted from the render
                html_text += self.raw_text[:first_clause_range[0]] + first_clause_render
            html_text += overlap_render
            if overlap_range[1] < (len(self.raw_text) - 1):
                # If both clauses end at the end of the text, the second clause can be omitted from the render
                html_text += second_clause_render + self.raw_text[second_clause_range[1] + 1:]
        else:
            first_clause_text = self.raw_text[first_clause_range[0]:first_clause_range[1] + 1]
            first_clause_render = f"<span class=\"first_clause\">{first_clause_text}</span>"
            second_clause_text = self.raw_text[second_clause_range[0]:second_clause_range[1] + 1]
            second_clause_render = f"<span class=\"second_clause\">{second_clause_text}</span>"

            html_text = (self.raw_text[:first_clause_range[0]] + first_clause_render +
                         self.raw_text[first_clause_range[1] + 1:second_clause_range[0]] +
                         second_clause_render + self.raw_text[second_clause_range[1] + 1:])

        return html_text

    def set_clause_a_range(self, clause_a_range: tuple[int, int] | None):
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
            raise TypeError("clause_a_range must be a tuple")
        if len(clause_a_range) != 2:
            raise ValueError("clause_a_range must contain exactly two elements")
        if (type(clause_a_range[0]) is not int) or (type(clause_a_range[1]) is not int):
            raise TypeError("clause_a_range must only contain integers")
        if clause_a_range[1] <= clause_a_range[0]:
            raise ValueError("The second integer of clause_a_range must be greater than the second integer")

        self.clause_a_range = clause_a_range

    def set_clause_b_range(self, clause_b_range: tuple[int, int] | None):
        """
        Sets the character index range for Clause B.
        The range defined is inclusive. The second integer must be greater than the first.
        Parameters
        ----------
        clause_b_range: tuple[int, int] - The start and end index of range defined for Clause B
        """
        if clause_b_range is None:
            self.clause_a_range = clause_b_range
            return
        if type(clause_b_range) is not tuple:
            raise TypeError("clause_b_range must be a tuple")
        if len(clause_b_range) != 2:
            raise ValueError("clause_b_range must contain exactly two elements")
        if (type(clause_b_range[0]) is not int) or (type(clause_b_range[1]) is not int):
            raise TypeError("clause_b_range must only contain integers")
        if clause_b_range[1] <= clause_b_range[0]:
            raise ValueError("The second integer of clause_b_range must be greater than the second integer")

        self.clause_b_range = clause_b_range


class TextDisplay:
    """
    Controls the text view and rendering
    """
    def __init__(self):
        self.prev_paragraph = ContextParagraph()
        self.next_paragraph = ContextParagraph()
        self.curr_paragraph = CurrentParagraph()
        self.component = Column(
            HTML(self.prev_paragraph, styles=context_paragraph_style),
            HTML(self.curr_paragraph, styles=curr_paragraph_style, stylesheets=[clause_stylesheet]),
            HTML(self.next_paragraph, styles=context_paragraph_style),
            styles=text_display_style,
            sizing_mode="stretch_width"
        )

    def get_component(self):
        return self.component

    def set_curr_paragraph_text(self, text: str):
        self.curr_paragraph.set_text(text)

    def set_prev_paragraph_text(self, text: str):
        self.prev_paragraph.set_text(text)

    def set_next_paragraph_text(self, text: str):
        self.next_paragraph.set_text(text)

    def set_clause_a_range(self, clause_a_range: tuple[int, int] | None):
        """
        Calls the method of the same name on the current paragraph object (unless curr_paragraph is None)
        """
        if self.curr_paragraph is not None:
            self.curr_paragraph.set_clause_a_range(clause_a_range)

    def set_clause_b_range(self, clause_b_range: tuple[int, int] | None):
        """
        Calls the method of the same name on the current paragraph object (unless curr_paragraph is None)
        """
        if self.curr_paragraph is not None:
            self.curr_paragraph.set_clause_b_range(clause_b_range)
