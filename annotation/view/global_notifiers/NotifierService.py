import panel


class NotifierService:
    def notify_error(self, error_msg: str):
        panel.state.notifications.error(error_msg, duration=0)

    def notify_success(self, success_msg: str):
        panel.state.notifications.success(success_msg, duration=0)
