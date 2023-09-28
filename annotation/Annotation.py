from annotation.controller.AnnotationController import AnnotationController
from annotation.model.AnnotationService import AnnotationService
from annotation.view.AnnotationViewWrapper import AnnotationViewWrapper


class Annotation:
    def __init__(self, paragraph_db_path: str, clause_db_path: str):
        self.service: AnnotationService = AnnotationService(paragraph_db_path, clause_db_path)
        self.controller: AnnotationController = AnnotationController(self.service)
        self.view: AnnotationViewWrapper = AnnotationViewWrapper(self.controller)

    def run(self):
        return self.view.get_layout().servable()
