from typing import Optional

import panel as pn
from pandas import DataFrame
from panel import Column
import plotly.express as px
from panel.pane import Plotly
from plotly.graph_objs import Figure
import plotly.graph_objects as go

from annotation.controller import AnnotationController


pn.extension('plotly')


class FigureGenerator:
    CLASS_ORDER: list[str] = ['NA', 'INC', 'COH', 'REP', 'REI', 'SEQ', 'CON', 'SUB', 'INT']

    @staticmethod
    def create_scatterplot(df: DataFrame) -> Optional[Figure]:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["sequence_position"],
                y=df["classification"],
                mode="lines+markers"
            )
        )

        # Update layout
        fig.update_layout(
            xaxis_title="Sequence Position",
            yaxis_title="Classification",
            yaxis=dict(
                categoryorder="array",
                categoryarray=FigureGenerator.CLASS_ORDER,
                showticklabels=True
            ),
            showlegend=False
        )

        return fig

    @staticmethod
    def create_bar_chart(df: DataFrame) -> Optional[Figure]:
        plot_df = df.groupby(['classification']).size().reset_index(name='count')
        fig = px.bar(plot_df, x='classification', y='count', color='classification')

        return fig


class DataDisplay:
    """
    Controls the data view and rendering
    """
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller
        self.component = Column(sizing_mode='stretch_width')

        self.controller.add_update_text_display_callable(self.update_display)

    def update_display(self):
        df: Optional[DataFrame] = self.controller.get_plot_data()
        if df is None:
            self.component.objects = []
            return
        scatterplot: Figure = FigureGenerator.create_scatterplot(df)
        barchart: Figure = FigureGenerator.create_bar_chart(df)
        self.component.objects = [
            Plotly(scatterplot, sizing_mode='stretch_width'),
            Plotly(barchart, sizing_mode='stretch_width')
        ]

    def get_component(self):
        return self.component
