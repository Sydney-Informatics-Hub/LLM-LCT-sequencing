import panel


class NotifierService:
    def __init__(self):
        panel.extension(notifications=True)

    def notify_error(self, error_msg: str, duration: int = 0):
        if panel.state.notifications is not None:
            panel.state.notifications.error(error_msg, duration)

    def notify_success(self, success_msg: str, duration: int = 5000):
        if panel.state.notifications is not None:
            panel.state.notifications.success(success_msg, duration)

    def notify_info(self, info_msg: str, duration: int = 5000):
        if panel.state.notifications is not None:
            panel.state.notifications.info(info_msg, duration)

    def clear_all(self):
        if panel.state.notifications is not None:
            panel.state.notifications.clear()
