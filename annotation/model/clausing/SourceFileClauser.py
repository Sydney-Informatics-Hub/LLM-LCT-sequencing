from io import BytesIO

from pandas import DataFrame

import spacy
from spacy.tokens.doc import Doc
from docx import Document
from docx.table import Table

CLAUSE_FIELD: str = "clause"
START_FIELD: str = "start_idx"
END_FIELD: str = "end_idx"


class SourceFileClauser:
    NLP = spacy.load("en_core_web_sm")

    def __init__(self, source_file: BytesIO, filetype: str):
        self.source_text: str
        if filetype == "docx":
            self.source_text = SourceFileClauser.read_docx(source_file)
        elif filetype == "txt":
            self.source_text = SourceFileClauser.read_txt(source_file)
        else:
            raise ValueError(f"File type {filetype} is not a valid source file type")

    def get_text(self) -> str:
        return self.source_text

    @staticmethod
    def read_docx(docx_file: BytesIO) -> str:
        docx_file.seek(0)
        try:
            doc = Document(docx_file)
        except Exception:
            raise ValueError("Loaded file type or file format is incorrect")
        doc_text: str = ""

        if len(doc.tables) == 0:
            raise ValueError("No table found within the loaded document")

        text_table: Table = doc.tables[0]

        content_col: int = -1
        for idx, cell in enumerate(text_table.rows[0].cells):
            if cell.text.lower() == "content":
                content_col = idx

        if content_col == -1:
            raise ValueError("No column labelled 'content' found in table")

        for row in text_table.rows[1:]:
            cell = row.cells[content_col]
            doc_text += f"{cell.text} \n"

        return doc_text

    @staticmethod
    def read_txt(txt_file: BytesIO) -> str:
        txt_file.seek(0)
        txt_bytes: bytes = txt_file.read()
        try:
            txt_content: str = txt_bytes.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("Text file must be encoded in UTF-8")

        return txt_content

    @staticmethod
    def _get_clause_subtrees(doc: Doc) -> list[tuple[int, int, list]]:
        clause_subtrees: list[tuple[int, int, list]] = []
        for tok in doc:
            if tok.pos_ == 'VERB' or tok.dep_ == "ROOT":
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
        for start_idx, end_idx, subtree_toks in SourceFileClauser._get_clause_subtrees(doc):
            item = {START_FIELD: start_idx, END_FIELD: end_idx,
                    CLAUSE_FIELD: ''.join(tok.text_with_ws
                                      for tok in subtree_toks
                                      if not tok.is_space)}
            items.append(item)

        return items

    def generate_clause_dataframe(self) -> DataFrame:
        doc = SourceFileClauser.NLP(self.source_text)
        clauses: list[dict] = SourceFileClauser._get_clause_items(doc)

        return DataFrame(clauses, columns=["clause", "start_idx", "end_idx"])
