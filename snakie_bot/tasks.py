import asyncio
from typing import TextIO

from celery import shared_task

from user.sender import UserSender


@shared_task
def send_to_user_task(to_user: str, user_pk: int, message_text: str, with_keyboard: bool = False, image_io: TextIO | None = None):
    asyncio.run(UserSender.send_to_user(to_user, user_pk, message_text, with_keyboard, image_io))
