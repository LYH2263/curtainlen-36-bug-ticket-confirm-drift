"""Feature modules."""


class TicketError(Exception):
    """算料票领域错误；由路由层翻译成 HTTP 响应。"""

    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
