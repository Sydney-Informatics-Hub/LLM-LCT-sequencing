from annotation.view.AnnotationViewWrapper import AnnotationViewWrapper


class AnnotationModel:
    pass


class AnnotationController:
    def __init__(self):
        self.model = AnnotationModel()
        self.view = AnnotationViewWrapper()

    def get_widget(self):
        return self.view.serve_widget()
