from django.db import models

NULLABLE = {"blank": True, "null": True}
NOT_NULLABLE = {"blank": False, "null": False}


class User(models.Model):
    chat_id = models.BigIntegerField(
        verbose_name='Chat id',
        **NOT_NULLABLE
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=100,
        **NULLABLE
    )
    state = models.CharField(
        verbose_name='Статус в переписке в боте',
        max_length=50,
        default="NEW",
    )
    last_visit_time = models.DateTimeField(
        verbose_name='Дата и время последнего посещения',
        auto_now=True,
    )
    registration_datetime = models.DateTimeField(
        verbose_name='Даты и время регистрации',
        auto_now_add=True,
    )
    first_sub_date = models.DateTimeField(
        verbose_name='Дата первой подписки',
        **NULLABLE,
    )

    is_superuser = models.BooleanField(
        verbose_name='Администратор?',
        **NOT_NULLABLE,
        default=False,
    )

    def __str__(self) -> str:
        return f"{self.username if self.username else self.chat_id}"

    async def is_subscribe(self):
        return self.subscriptions.filter(is_active=True).aexists()

    @property
    def link(self):
        return f"https://t.me/{self.username}" if self.username else f"https://web.telegram.org/k/#{self.chat_id}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
