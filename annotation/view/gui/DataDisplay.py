from typing import Optional

import panel as pn
from pandas import DataFrame
from panel import Column
import plotly.express as px
from panel.pane import Plotly
from panel.widgets import IntSlider
from plotly.graph_objs import Figure
import plotly.graph_objects as go

from annotation.controller import AnnotationController


pn.extension('plotly')


class FigureGenerator:
    CLASS_ORDER: list[str] = ['NA', 'INC', 'COH', 'REP', 'REI', 'SEQ', 'CON', 'SUB', 'INT']

    @staticmethod
    def create_scatterplot(df: DataFrame) -> Figure:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["sequence_position"],
                y=df["classification"],
                mode="lines+markers"
            )
        )

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
    def create_weighted_scatterplot(df: DataFrame, window: Optional[int] = None) -> Figure:
        if window is None:
            window = len(df) // 10
        df["rolling_average"] = df.rolling(window=window, center=True)['weight'].mean()

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["sequence_position"],
                y=df["rolling_average"],
                mode="lines"
            )
        )

        fig.update_layout(
            xaxis_title="Sequence Position",
            yaxis_title="EC",
            yaxis=dict(
                categoryorder="array",
                categoryarray=FigureGenerator.CLASS_ORDER,
                showticklabels=False
            ),
            showlegend=False
        )

        return fig

    @staticmethod
    def create_bar_chart(df: DataFrame) -> Figure:
        plot_df = df.groupby(['classification']).size().reset_index(name='count')
        fig = px.bar(plot_df, x='classification', y='count', color='classification')

        return fig


class DataDisplay:
    """
    Controls the data view and rendering
    """
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller

        self.scatterplot = Plotly(sizing_mode='stretch_width', visible=False)
        self.weighted_scatterplot = Plotly(sizing_mode='stretch_width', visible=False)
        self.average_window_slider = IntSlider(name='Average Window', start=1, end=500, step=1, value=1, visible=False)
        self.bar_chart = Plotly(sizing_mode='stretch_width', visible=False)

        self.component = Column(
            self.scatterplot,
            self.weighted_scatterplot,
            self.average_window_slider,
            self.bar_chart,
            sizing_mode='stretch_width')

        self.average_window_slider.param.watch(self._rolling_average_slider_update, ['value'])
        self.controller.add_update_text_display_callable(self.update_display)

    def update_display(self):
        df: Optional[DataFrame] = self.controller.get_plot_data()
        weights_df: Optional[DataFrame] = self.controller.get_plot_weights_data()
        if weights_df is not None:
            window = self.average_window_slider.value
            self.weighted_scatterplot.object = FigureGenerator.create_weighted_scatterplot(weights_df, window)
        if df is not None:
            self.scatterplot.object = FigureGenerator.create_scatterplot(df)
            self.bar_chart.object = FigureGenerator.create_bar_chart(df)

        self.average_window_slider.visible = weights_df is not None
        self.weighted_scatterplot.visible = weights_df is not None
        self.scatterplot.visible = df is not None
        self.bar_chart.visible = df is not None

    def _rolling_average_slider_update(self, *_):
        weights_df: Optional[DataFrame] = self.controller.get_plot_weights_data()
        if weights_df is not None:
            window = self.average_window_slider.value
            self.weighted_scatterplot.object = FigureGenerator.create_weighted_scatterplot(weights_df, window)

    def get_component(self):
        return self.component
