from annotation.controller.AnnotationController import AnnotationController
from annotation.model.AnnotationService import AnnotationService
from annotation.view.AnnotationViewWrapper import AnnotationViewWrapper


class Annotation:
    def __init__(self):
        self.service = AnnotationService()
        self.controller = AnnotationController(self.service)
        self.view = AnnotationViewWrapper(self.controller)

    def run(self):
        return self.view.get_layout().servable()
