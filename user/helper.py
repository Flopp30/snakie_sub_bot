class CustomCounter:
    _report_message: str = (
        '{success_counter} сообщений отправлено успешно. '
        '{error_counter} - не отправлены. '
        '{block_counter} - бот заблокирован.'
    )

    def __init__(self):
        self.success_counter: int = 0
        self.error_counter: int = 0
        self.block_counter: int = 0

    @property
    def report_message(self):
        return self._report_message.format(
            success_counter=self.success_counter,
            error_counter=self.error_counter,
            block_counter=self.block_counter
        )
