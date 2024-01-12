import asyncio
import json
import logging

import aiohttp
import requests
from django.conf import settings

from bot_parts.models import OwnedChat, OwnedBotsInMemory, OwnedChatInMemory
from user.models import User

logger = logging.getLogger(__name__)


def get_tg_payload(chat_id, message_text, buttons: [{str: str}] = None):
    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'HTML',
    }
    if buttons:
        keyboard_buttons = []
        for button in buttons:
            for text, url in button.items():
                keyboard_buttons.append({
                    "text": text,
                    "url": url
                })
        payload['reply_markup'] = {'inline_keyboard': [[keyboard_button] for keyboard_button in keyboard_buttons]}
    return payload


def get_tg_payload_with_callbacks(chat_id, message_text, buttons: [{str: str}]):
    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'HTML',
    }
    if buttons:
        keyboard_buttons = []
        for button in buttons:
            for text, callback in button.items():
                keyboard_buttons.append({
                    "text": text,
                    "callback_data": callback
                })
        payload['reply_markup'] = {'inline_keyboard': [[keyboard_button] for keyboard_button in keyboard_buttons]}
    return payload


async def asend_tg_message_to_admins_from_django(text: str):
    async with aiohttp.ClientSession() as session:
        async for chat_id in User.objects.filter(is_superuser=True).values_list('chat_id', flat=True):
            payload = get_tg_payload(chat_id=chat_id, message_text=text)
            response = await session.post(settings.TG_SEND_MESSAGE_URL, json=payload)
            if response.status != 200:
                logger.error(f'Не удалось отправить сообщение: {payload}\n{response.text}')


def send_tg_message_to_admins_from_django(text: str):
    admins_chat_id = User.objects.filter(is_superuser=True).values_list('chat_id', flat=True)
    for chat_id in admins_chat_id:
        payload = get_tg_payload(chat_id=chat_id, message_text=text)
        response = requests.post(settings.TG_SEND_MESSAGE_URL, json=payload)
        if response.status_code != 200:
            logger.error(f'Не удалось отправить сообщение: {payload}\n{response.text}')


async def aban_user_in_owned_bots(user_chat_id):
    """
        Ban user's in owned bots
    """
    owned_bots = await OwnedBotsInMemory.abots()
    for owned_bot in owned_bots:
        ban_url = owned_bot.get_ban_url(user_id=user_chat_id)
        async with aiohttp.ClientSession() as aio_session:
            response = await aio_session.get(ban_url, headers=settings.HEADERS)
            response_text = await response.text()
            status_code = json.loads(response_text).get("code")
            if status_code != 0:
                await asend_tg_message_to_admins_from_django(
                    f"Проблема с баном пользователя: chat_id {user_chat_id} в боте {owned_bot.name}\n"
                    f"response: {response_text}"
                )
                logger.error(f"Something went wrong. Can't banned user {user_chat_id} in bot {owned_bot.name}")
            else:
                logger.info(f"User {user_chat_id} was banned in bot {owned_bot.name}")

    tasks = []
    owned_chats = await OwnedChatInMemory.achats()
    async with aiohttp.ClientSession() as aio_session:
        for chat in owned_chats:
            task = asyncio.create_task(kick_chat_member(chat, aio_session, user_chat_id))
            tasks.append(task)
        await asyncio.gather(*tasks)


async def kick_chat_member(chat: OwnedChat, aio_session, user_chat_id):
    """
        Kick user from owned chats
    """
    response = await aio_session.post(
        settings.TG_BAN_URL,
        data={
            "chat_id": chat.chat_id,
            "user_id": user_chat_id,
        }
    )
    if str(response.status) == '200':
        logger.info(f'Пользователь {user_chat_id} успешно удален из чата {chat.name}')
    else:
        await asend_tg_message_to_admins_from_django(
            f"Проблема с киком пользователя: chat_id {user_chat_id} в чате {chat.name}\n\n"
            f"response: {await response.text()}\n"
        )


async def aunban_user_in_owned_bots(user_chat_id):
    """
        Unban user in owned bots
    """
    owned_bots = await OwnedBotsInMemory.abots()
    for owned_bot in owned_bots:
        unban_url = owned_bot.get_unban_url(user_id=user_chat_id)
        async with aiohttp.ClientSession() as aio_session:
            response = await aio_session.get(unban_url, headers=settings.HEADERS)
            response_text = await response.text()
            status_code = json.loads(response_text).get("code")
            if status_code != 0:
                await asend_tg_message_to_admins_from_django(
                    f"Проблема с разблокировкой пользователя пользователя: chat_id {user_chat_id} "
                    f"в боте {owned_bot.name}\n"
                    f"response: {response_text}"
                )
                logger.error(f"Something went wrong. Can't unbanned user {user_chat_id} in bot {owned_bot.name}")
            else:
                logger.info(f"User {user_chat_id} was unbanned in bot {owned_bot.name}")

    tasks = []
    owned_chats = await OwnedChatInMemory.achats()
    async with aiohttp.ClientSession() as aio_session:
        for chat in owned_chats:
            task = asyncio.create_task(add_chat_member(chat, aio_session, user_chat_id))
            tasks.append(task)
        await asyncio.gather(*tasks)


async def add_chat_member(chat: OwnedChat, aio_session, user_chat_id):
    """
        add user in owned chat
    """
    response = await aio_session.post(
        settings.TG_UNBAN_URL,
        data={
            "chat_id": chat.chat_id,
            "user_id": user_chat_id,
        }
    )
    if str(response.status) == '200':
        logger.info(f'Пользователь {user_chat_id} успешно добавлен в чат {chat.name}')
    else:
        await asend_tg_message_to_admins_from_django(
            f"Проблема с добавление пользователя: chat_id {user_chat_id} в чат {chat.name}\n\n"
            f"response: {await response.text()}\n"
        )


def ban_user_in_owned_bots(user_chat_id):
    for owned_bot in OwnedBotsInMemory.bots():
        ban_url = owned_bot.get_ban_url(user_id=user_chat_id)
        response = requests.get(ban_url, headers=settings.HEADERS)
        status_code = json.loads(response.text).get("code")
        if status_code != 0:
            send_tg_message_to_admins_from_django(
                f"Проблема с баном пользователя: chat_id {user_chat_id} в боте {owned_bot.name}\n"
                f"response: {response.text}"
            )
            logger.error(f"Something went wrong. Can't banned user {user_chat_id} in bot {owned_bot.name}")
        else:
            logger.info(f"User {user_chat_id} was banned in bot {owned_bot.name}")

    for chat in OwnedChatInMemory.chats():
        ban_chat_member(chat, user_chat_id)


def ban_chat_member(chat: OwnedChat, user_chat_id):
    response = requests.post(
        settings.TG_BAN_URL,
        data={
            "chat_id": chat.chat_id,
            "user_id": user_chat_id,
        }
    )
    if str(response.status_code) == '200':
        logger.info(f'Пользователь {user_chat_id} успешно удален из чата {chat.name}')
    else:
        send_tg_message_to_admins_from_django(
            f"Проблема с киком пользователя: chat_id {user_chat_id} из чата {chat.name}\n\n"
            f"response: {response.text}"
        )


def unban_user_in_owned_bots(user_chat_id):
    for owned_bot in OwnedBotsInMemory.bots():
        unban_url = owned_bot.get_unban_url(user_id=user_chat_id)
        response = requests.get(unban_url, headers=settings.HEADERS)
        status_code = json.loads(response.text).get("code")
        if status_code != 0:
            send_tg_message_to_admins_from_django(
                f"Проблема с разблокировкой пользователя: chat_id {user_chat_id} в боте {owned_bot.name}\n\n"
                f"response: {response.text}"
            )
            logger.error(f"Something went wrong. Can't unban user {user_chat_id} in bot {owned_bot.name}\n\n"
                         f"response: {response.text}")
        else:
            logger.error(f"User {user_chat_id} was unbanned in bot {owned_bot.name}")

    for chat in OwnedChatInMemory.chats():
        unban_chat_member(chat, user_chat_id)


def unban_chat_member(chat: OwnedChat, user_chat_id):
    response = requests.post(
        settings.TG_UNBAN_URL,
        data={
            "chat_id": chat.chat_id,
            "user_id": user_chat_id,
        }
    )
    if str(response.status_code) == '200':
        logger.info(f'Пользователь {user_chat_id} успешно разблокирован в чате {chat.name}')
    else:
        send_tg_message_to_admins_from_django(
            f"Проблема со снятием бана у пользователя: chat_id {user_chat_id} в чате {chat.name}"
            f"response: {response.text}"
        )
