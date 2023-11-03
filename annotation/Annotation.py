from annotation.controller.AnnotationController import AnnotationController
from annotation.model.AnnotationService import AnnotationService
from annotation.model.export import ExportService
from annotation.view.AnnotationViewWrapper import AnnotationViewWrapper
from annotation.view.global_notifiers import NotifierService


class Annotation:
    def __init__(self, log_file_path: str):
        annotation_service: AnnotationService = AnnotationService()
        controller: AnnotationController = AnnotationController(annotation_service, NotifierService(),
                                                                ExportService(), log_file_path, debug=True)
        self.view: AnnotationViewWrapper = AnnotationViewWrapper(controller)

    def run(self):
        return self.view.get_layout().servable()
