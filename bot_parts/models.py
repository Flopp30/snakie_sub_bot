from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from user.models import NOT_NULLABLE, NULLABLE


class OwnedBot(models.Model):
    name = models.CharField(
        verbose_name='Имя бота',
        default='Unnamed Bot',
        max_length=128,
        **NULLABLE,
    )
    api_token = models.CharField(
        verbose_name='Ключ API',
        max_length=128,
        **NOT_NULLABLE
    )
    chat_id = models.BigIntegerField(
        verbose_name='Чат id бота в tg',
        **NOT_NULLABLE
    )

    class Meta:
        verbose_name = 'Бот'
        verbose_name_plural = 'Боты'

    def get_ban_url(self, user_id: int) -> str:
        return f"https://api.puzzlebot.top/" \
               f"?token={self.api_token}&method=userBan" \
               f"&tg_chat_id={self.chat_id}&user_id={user_id}&until_date=1988150461"

    def get_unban_url(self, user_id: int) -> str:
        return f"https://api.puzzlebot.top/" \
               f"?token={self.api_token}&method=userUnban" \
               f"&tg_chat_id={self.chat_id}&user_id={user_id}"


class OwnedBotsInMemory:
    _bots = []

    @classmethod
    async def abots(cls):
        if not cls._bots:
            await cls.areload_bots()
        return cls._bots

    @classmethod
    async def areload_bots(cls, *args, **kwargs):
        cls._bots = []
        async for bot in OwnedBot.objects.all():
            cls._bots.append(bot)

    @classmethod
    def bots(cls):
        # TODO remove all sync methods, when will you transfer payment views to async
        if not cls._bots:
            cls.reload_bots()
        return cls._bots

    @classmethod
    def reload_bots(cls):
        cls._bots = []
        for bot in OwnedBot.objects.all():
            cls._bots.append(bot)


class OwnedChat(models.Model):
    name = models.CharField(
        verbose_name='Название чата',
        max_length=128,
        default='Unnamed chat',
        **NULLABLE,
    )
    chat_id = models.BigIntegerField(
        verbose_name='Чат ID в tg',
        primary_key=True,
    )

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'


class OwnedChatInMemory:
    _chats = []

    @classmethod
    async def achats(cls):
        if not cls._chats:
            await cls.areload_chats()
        return cls._chats

    @classmethod
    async def areload_chats(cls, *args, **kwargs):
        cls._chats = []
        async for chat in OwnedChat.objects.all():
            cls._chats.append(chat)

    @classmethod
    def chats(cls):
        if not cls._chats:
            cls.reload_chats()
        return cls._chats

    @classmethod
    def reload_chats(cls):
        cls._chats = []
        for chat in OwnedChat.objects.all():
            cls._chats.append(chat)


class AfterPaymentContent(models.Model):
    name = models.CharField(
        verbose_name='Отображаемое имя ссылки',
        max_length=128,
        default='Unnamed chat',
        **NULLABLE,
    )
    link = models.CharField(
        verbose_name='Ссылка на контент',
        max_length=128,
        default='https://google.com/',
        **NULLABLE,
    )

    class Meta:
        verbose_name = 'Оплачиваемый контент'
        verbose_name_plural = 'Оплачиваемый контент'


class ContentInMemory:
    _contents: list = []

    @classmethod
    def content(cls):
        if not cls._contents:
            cls.load_contents()
        return cls._contents

    @classmethod
    def load_contents(cls, *args, **kwargs):
        cls._contents = []
        for content in AfterPaymentContent.objects.all():
            cls._contents.append(content)

    @classmethod
    async def acontent(cls):
        if not cls._contents:
            await cls.aload_contents()
        return cls._contents

    @classmethod
    async def aload_contents(cls, *args, **kwargs):
        cls._contents = []
        async for content in AfterPaymentContent.objects.all():
            cls._contents.append(content)


class SalesDate(models.Model):
    is_active = models.BooleanField('Активна?', default=False, **NOT_NULLABLE)
    start_date = models.DateTimeField('Старт', **NOT_NULLABLE)
    end_date = models.DateTimeField('Конец', **NOT_NULLABLE)

    class Meta:
        verbose_name = 'Дата продаж'
        verbose_name_plural = 'Даты продаж'
        unique_together = ['start_date', 'end_date']

    def __str__(self):
        return f"Продажи {self.start_date} -> {self.end_date}"

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError('Дата старта продаж должна быть строго меньше даты конца продаж')
        existing_records = SalesDate.objects.filter(
            Q(start_date__lte=self.start_date, end_date__gte=self.start_date) & ~Q(pk=self.pk)
        )
        if existing_records.exists():
            raise ValidationError('Продажи на этот период уже есть')


class SalesInMemory:
    is_available: bool = False

    @classmethod
    async def update_sales_is_available(cls, *args, **kwargs):
        now_ = timezone.now()
        try:
            await SalesDate.objects.aget(start_date__lte=now_, end_date__gte=now_, is_active=True)
            cls.is_available = True
        except SalesDate.DoesNotExist:
            cls.is_available = False
