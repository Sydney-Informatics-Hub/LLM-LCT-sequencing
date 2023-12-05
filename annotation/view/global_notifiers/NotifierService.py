import panel


class NotifierService:
    def notify_error(self, error_msg: str, duration: int = 0):
        panel.state.notifications.error(error_msg, duration)

    def notify_success(self, success_msg: str, duration: int = 0):
        panel.state.notifications.success(success_msg, duration)

    def clear_all(self):
        panel.state.notifications.clear()
