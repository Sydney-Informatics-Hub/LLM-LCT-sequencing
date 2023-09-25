from annotation.controller.AnnotationController import AnnotationController
from annotation.model.AnnotationModel import AnnotationModel
from annotation.view.AnnotationViewWrapper import AnnotationViewWrapper


class Annotation:
    def __init__(self):
        self.model = AnnotationModel()
        self.controller = AnnotationController(self.model)
        self.view = AnnotationViewWrapper(self.controller)

    def run(self):
        return self.view.get_widgets().servable()
