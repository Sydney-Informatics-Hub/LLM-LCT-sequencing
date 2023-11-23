from pandas import DataFrame

CLAUSE_FIELD: str = "clause"
START_FIELD: str = "start_idx"
END_FIELD: str = "end_idx"


class SequencingTool:
    SEQUENCE_ID_FIELD: str = "sequence_id"
    C1_START_FIELD: str = "c1_start"
    C1_END_FIELD: str = "c1_end"
    C2_START_FIELD: str = "c2_start"
    C2_END_FIELD: str = "c2_end"

    CLAUSE_PAIR_RANGE: int = 1

    def __init__(self, clause_df: DataFrame):
        self.clause_df: DataFrame = clause_df

    def generate_sequence_df(self) -> DataFrame:
        sequences: list[dict] = []
        seq_id: int = 1
        for idx, clause_a in self.clause_df.iterrows():
            curr_seq_idx: int = int(idx)
            for i in range(curr_seq_idx+1, curr_seq_idx+SequencingTool.CLAUSE_PAIR_RANGE+1):
                try:
                    clause_b = self.clause_df.iloc[i]
                except IndexError:
                    continue

                sequence: dict = {
                    SequencingTool.SEQUENCE_ID_FIELD: seq_id,
                    SequencingTool.C1_START_FIELD: int(clause_a[START_FIELD]),
                    SequencingTool.C1_END_FIELD: int(clause_a[END_FIELD]),
                    SequencingTool.C2_START_FIELD: int(clause_b[START_FIELD]),
                    SequencingTool.C2_END_FIELD: int(clause_b[END_FIELD]),
                }
                seq_id += 1

                sequences.append(sequence)

        return DataFrame(sequences, dtype=int)
