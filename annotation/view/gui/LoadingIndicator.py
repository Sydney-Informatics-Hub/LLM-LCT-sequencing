from typing import Optional

from panel import Row
from panel.widgets import LoadingSpinner

from annotation.controller import AnnotationController


class LoadingIndicator:
    def __init__(self, controller: AnnotationController):
        self.controller: AnnotationController = controller
        self.loading_indicator: LoadingSpinner = LoadingSpinner(size=50, value=True, color="success", bgcolor="dark")

        self.component = Row(self.loading_indicator,
                             visible=False,
                             align="center")

        self.controller.add_update_text_display_callable(self.update_display)

    def get_component(self):
        return self.component

    def update_display(self):
        loading_msg: Optional[str] = self.controller.get_loading_msg()
        if loading_msg is None:
            self.component.visible = False
        else:
            self.loading_indicator.name = loading_msg
            self.component.visible = True
