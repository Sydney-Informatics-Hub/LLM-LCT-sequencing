from annotation.controller.AnnotationController import AnnotationController
from annotation.model.AnnotationService import AnnotationService
from annotation.view.AnnotationViewWrapper import AnnotationViewWrapper
from annotation.view.notifications import NotifierService


class Annotation:
    def __init__(self, text_database_path: str, clause_db_path: str, sequence_db_path: str, log_file_path: str):
        self.annotation_service: AnnotationService = AnnotationService(text_database_path,
                                                                       clause_db_path,
                                                                       sequence_db_path)
        self.notifier_service: NotifierService = NotifierService()
        self.controller: AnnotationController = AnnotationController(self.annotation_service, self.notifier_service,
                                                                     log_file_path, debug=False)
        self.view: AnnotationViewWrapper = AnnotationViewWrapper(self.controller)

    def run(self):
        return self.view.get_layout().servable()
