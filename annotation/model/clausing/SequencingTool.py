from pandas import DataFrame

CLAUSE_FIELD: str = "clause"
START_FIELD: str = "start_idx"
END_FIELD: str = "end_idx"

SEQUENCE_ID_FIELD: str = "sequence_id"
C1_START_FIELD: str = "c1_start"
C1_END_FIELD: str = "c1_end"
C2_START_FIELD: str = "c2_start"
C2_END_FIELD: str = "c2_end"

CLAUSE_PAIR_RANGE: int = 1


class SequencingTool:
    def __init__(self, clause_df: DataFrame):
        self.clause_df: DataFrame = clause_df

    def _generate_groupings(self, item_df: DataFrame, item_range: int) -> list[dict]:
        groupings: list[dict] = []
        for idx, item_a in item_df.iterrows():
            idx: int
            curr_seq_idx: int = int(idx)
            for i in range(curr_seq_idx + 1, curr_seq_idx + item_range + 1):
                try:
                    item_b = item_df.iloc[i]
                except IndexError:
                    continue

                grouping: dict = {
                    C1_START_FIELD: int(item_a[START_FIELD]),
                    C1_END_FIELD: int(item_a[END_FIELD]),
                    C2_START_FIELD: int(item_b[START_FIELD]),
                    C2_END_FIELD: int(item_b[END_FIELD]),
                }
                groupings.append(grouping)

        return groupings

    def generate_initial_sequence_df(self) -> DataFrame:
        sequences: list[dict] = self._generate_groupings(self.clause_df, CLAUSE_PAIR_RANGE)
        sequences.sort(key=lambda s: (s[C1_START_FIELD], s[C1_END_FIELD], s[C2_START_FIELD], s[C2_END_FIELD]))

        for seq_idx, seq in enumerate(sequences):
            seq[SEQUENCE_ID_FIELD] = seq_idx + 1

        return DataFrame(sequences, dtype=int)
