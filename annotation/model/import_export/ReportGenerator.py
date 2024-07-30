from io import BytesIO

from matplotlib import pyplot as plt
from pandas import DataFrame, Series, get_dummies, concat, read_csv
from reportlab.lib import colors
from reportlab.platypus import Image, Table, TableStyle, SimpleDocTemplate


class ReportGenerator:
    COLUMN_ORDER: list[str] = ['INT', 'SUB', 'CON', 'SEQ', 'REI', 'REP', 'COH', 'INC', 'N/A']
    WEIGHTS_ORDINAL = Series({
        'INT': 4,
        'SUB': 3,
        'CON': 2,
        'SEQ': 1,
        'REI': 0,
        'REP': 0,
        'COH': -1,
        'INC': -2,
        'N/A': 0
    })
    WEIGHTS_SIMPLE = Series({
        'INT': 1,
        'SUB': 1,
        'CON': 1,
        'SEQ': 1,
        'REI': 0,
        'REP': 0,
        'COH': -1,
        'INC': -1,
        'N/A': 0
    })

    @staticmethod
    def generate_pdf_report(df: DataFrame) -> BytesIO:
        pdf_buffer = BytesIO()
        flowables: list = []

        pdf_doc = SimpleDocTemplate(pdf_buffer)
        flowables.append(ReportGenerator.create_frequency_table(df))
        flowables.append(ReportGenerator.create_frequency_plot_image(df))
        flowables.append(ReportGenerator.create_frequency_bidirectional_image(df, 'Class frequency area plot'))
        flowables.append(ReportGenerator.create_ec_worm_image(df, 'The EC Worm with ordinal weighting',
                                                              ReportGenerator.WEIGHTS_ORDINAL))
        flowables.append(ReportGenerator.create_ec_worm_image(df, 'The EC Worm with simple weighting',
                                                              ReportGenerator.WEIGHTS_SIMPLE))

        pdf_doc.build(flowables)
        pdf_buffer.seek(0)

        return pdf_buffer

    @staticmethod
    def get_density_over_sequences(class_series: Series, window: int = 25) -> DataFrame:
        dummies_df = get_dummies(class_series)
        na_col = dummies_df.pop('-')
        dummies_df.insert(len(dummies_df.columns), 'N/A', na_col)
        dummies_df = dummies_df[ReportGenerator.COLUMN_ORDER]
        return (dummies_df.rolling(window).sum()
                .reindex()
                .fillna(0) * 2
                )

    @staticmethod
    def create_frequency_plot_image(df: DataFrame, colormap: str = 'viridis') -> Image:
        trimmed_df = df[['sequence_id', 'predicted_classes_name']]
        classes_df = ReportGenerator.get_density_over_sequences(trimmed_df['predicted_classes_name'])
        density_df = concat([df['sequence_id'], classes_df], axis=1)

        density_df.to_csv('density.csv', index=False)

        fig, ax = plt.subplots()
        density_df.plot.area(x='sequence_id', ax=ax, figsize=(8, 5),
                             colormap=colormap, title='Class frequency by sequence',
                             xlabel='Sequence order', ylabel='Rolling frequency')
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300)
        plt.close(fig)
        buf.seek(0)

        return Image(buf, useDPI=(300, 300))

    @staticmethod
    def create_frequency_bidirectional_image(df: DataFrame, title: str, colormap: str = 'winter') -> Image:
        trimmed_df = df[['sequence_id', 'predicted_classes_name']]
        classes_df = ReportGenerator.get_density_over_sequences(trimmed_df['predicted_classes_name'])
        classes_df = classes_df.drop(['REI', 'REP', 'N/A'], axis=1)
        classes_df[['COH', 'INC']] = -classes_df[['COH', 'INC']]
        density_df = concat([df['sequence_id'], classes_df], axis=1)

        fig, ax = plt.subplots()
        density_df.plot.area(x='sequence_id', ax=ax, figsize=(8, 4), legend=True, colormap=colormap,
                             title=title, xlabel='Sequence order', ylabel='Rolling frequency')
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300)
        plt.close(fig)
        buf.seek(0)

        return Image(buf, useDPI=(300, 300))

    @staticmethod
    def create_ec_worm_image(df: DataFrame, title: str, weighting: Series) -> Image:
        trimmed_df = df[['sequence_id', 'predicted_classes_name']]
        classes_df = ReportGenerator.get_density_over_sequences(trimmed_df['predicted_classes_name'])
        worm_df = DataFrame({'': classes_df.multiply(weighting).sum(axis=1)})
        density_df = concat([df['sequence_id'], worm_df], axis=1)

        fig, ax = plt.subplots()
        density_df.plot.line(x='sequence_id', ax=ax, figsize=(8, 4), legend=False,
                             title=title, xlabel='Sequence order', ylabel='Weighted EC')
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300)
        plt.close(fig)
        buf.seek(0)

        return Image(buf, useDPI=(300, 300))

    @staticmethod
    def get_frequency_sums(class_series: Series) -> DataFrame:
        dummies = get_dummies(class_series).sum()

        frequency_df = DataFrame(dummies)
        frequency_df = frequency_df.T
        na_col = frequency_df.pop('-')
        frequency_df.insert(len(frequency_df.columns), 'N/A', na_col)
        frequency_df = frequency_df[ReportGenerator.COLUMN_ORDER]
        frequency_df['Total'] = frequency_df.iloc[0].sum()

        percentage_proportion = (frequency_df.iloc[0, :-1] / frequency_df['Total'].values[0] * 100).round(1)
        frequency_df.loc[1] = percentage_proportion.tolist() + [100]

        frequency_df.insert(0, '', Series(['Count', 'Percentage']))

        return frequency_df

    @staticmethod
    def create_frequency_table(df: DataFrame) -> Table:
        frequency_df = ReportGenerator.get_frequency_sums(df['predicted_classes_name'])

        table_data = [frequency_df.columns.tolist()] + frequency_df.values.tolist()
        table = Table(table_data)

        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)

        return table

    @staticmethod
    def create_confusion_matrix(df: DataFrame) -> BytesIO:
        pass


if __name__ == "__main__":
    df = read_csv("/Users/hcro4489/My Drive/USYD SIH/Projects/LCT Classroom Interactions/sequence_annotation.csv")
    pdf_buf = ReportGenerator.generate_pdf_report(df)
    with open('test.pdf', 'wb') as f:
        f.write(pdf_buf.read())
