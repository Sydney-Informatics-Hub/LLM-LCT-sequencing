from io import BytesIO

from pandas import DataFrame

import spacy
from spacy.tokens.doc import Doc
from docx import Document
from docx.table import Table


class SourceFileLoader:
    NLP = spacy.load("en_core_web_sm")

    def __init__(self, source_file: str | BytesIO):
        self.source_text: str = SourceFileLoader.read_docx(source_file)

    def get_text(self) -> str:
        return self.source_text

    @staticmethod
    def read_docx(docx_file: str | BytesIO) -> str:
        doc = Document(docx_file)
        doc_text: str = ""

        text_table: Table = doc.tables[0]

        content_col: int = 0
        for idx, cell in enumerate(text_table.rows[0].cells):
            if cell.text.lower() == "content":
                content_col = idx

        for row in text_table.rows[1:]:
            cell = row.cells[content_col]
            doc_text += f"{cell.text}\n"

        return doc_text

    @staticmethod
    def _get_clause_subtrees(doc: Doc) -> list[tuple[int, int, list]]:
        clause_subtrees: list[tuple[int, int, list]] = []
        for tok in doc:
            if tok.pos_ == 'VERB':
                subtree_toks = []
                if tok.dep_ == 'aux':
                    continue
                for child in tok.children:
                    if child.dep_ == 'conj' or child.pos_ == 'CCONJ':
                        continue
                    subtree_toks.extend(child.subtree)
                subtree_toks.append(tok)
                subtree_toks.sort(key=lambda ch: ch.i)

                start_idx: int = subtree_toks[0].idx
                end_idx: int = subtree_toks[-1].idx + len(subtree_toks[-1].text)

                clause_subtree = start_idx, end_idx, subtree_toks
                clause_subtrees.append(tuple(clause_subtree))

        return sorted(clause_subtrees, key=lambda x: (x[2][0].i, -x[2][-1].i))

    @staticmethod
    def _get_clause_items(doc: Doc):
        items: list[dict] = []
        for start_idx, end_idx, subtree_toks in SourceFileLoader._get_clause_subtrees(doc):
            item = {'start_idx': start_idx, 'end_idx': end_idx,
                    'clause': ''.join(tok.text + tok.whitespace_
                                      for tok in subtree_toks
                                      if not tok.is_space)}
            items.append(item)

        return items

    def generate_clause_dataframe(self) -> DataFrame:
        doc = SourceFileLoader.NLP(self.source_text)
        clauses: list[dict] = SourceFileLoader._get_clause_items(doc)

        return DataFrame(clauses, columns=["clause", "start_idx", "end_idx"])