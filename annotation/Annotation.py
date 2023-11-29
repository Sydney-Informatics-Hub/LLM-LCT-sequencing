from annotation import log_file_path, llm_examples_path, llm_definitions_path, llm_zero_prompt_path
from annotation.controller.AnnotationController import AnnotationController
from annotation.model.AnnotationService import AnnotationService
from annotation.model.import_export import ImportExportService
from annotation.view.AnnotationViewWrapper import AnnotationViewWrapper
from annotation.view.global_notifiers import NotifierService


class Annotation:
    def __init__(self, debug: bool = False):
        annotation_service = AnnotationService()
        notifier_service = NotifierService()
        import_export_service = ImportExportService()
        controller: AnnotationController = AnnotationController(annotation_service, notifier_service,
                                                                import_export_service, llm_examples_path,
                                                                llm_definitions_path, llm_zero_prompt_path,
                                                                log_file_path, debug=debug)
        self.view: AnnotationViewWrapper = AnnotationViewWrapper(controller)

    def run(self):
        return self.view.get_layout().servable()
