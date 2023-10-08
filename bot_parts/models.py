from django.conf import settings
from django.db import models

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

    async def ban_user(self, aio_session, user_id):
        response = await aio_session.post(
            settings.TG_BAN_URL,
            data={
                "chat_id": self.chat_id,
                "user_id": user_id,
            }
        )
        return response.status_code

    async def unban_user(self, aio_session, user_id):
        response = await aio_session.post(
            settings.TG_UNBAN_URL,
            data={
                "chat_id": self.chat_id,
                "user_id": user_id,
            }
        )
        return response.status_code
