from annotation.controller.AnnotationController import AnnotationController
from annotation.model.AnnotationService import AnnotationService
from annotation.model.export import ExportService
from annotation.view.AnnotationViewWrapper import AnnotationViewWrapper
from annotation.view.notifications import NotifierService


class Annotation:
    def __init__(self, text_database_path: str, clause_db_path: str, sequence_db_path: str, log_file_path: str):
        annotation_service: AnnotationService = AnnotationService(text_database_path,
                                                                  clause_db_path,
                                                                  sequence_db_path)
        controller: AnnotationController = AnnotationController(annotation_service, NotifierService(),
                                                                ExportService(), log_file_path, debug=False)
        self.view: AnnotationViewWrapper = AnnotationViewWrapper(controller)

    def run(self):
        return self.view.get_layout().servable()
