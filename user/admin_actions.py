import json
import logging

import requests
from django.conf import settings
from django.contrib import messages

from bot_parts.models import OwnedBot
from utils.helpers import ban_user_in_owned_bots, unban_user_in_owned_bots, send_tg_message_to_admins_from_django


def block_in_all_bots(admin_model, request, queryset):
    success_counter = 0
    error_counter = 0
    for user in queryset:
        try:
            ban_user_in_owned_bots(user.chat_id)
        except Exception as e:
            error_counter += 1
            logging.error(e)
        else:
            success_counter += 1

    message = f"Заблокировано {success_counter} пользователей"
    if error_counter > 0:
        message += f" {error_counter} - с ошибкой"

    messages.success(request, message)


block_in_all_bots.short_description = "Ban: Заблокировать везде (боты + чаты)"


def unban_in_all_bots(admin_model, request, queryset):
    success_counter = 0
    error_counter = 0
    for user in queryset:
        try:
            unban_user_in_owned_bots(user.chat_id)
        except Exception as e:
            error_counter += 1
            logging.error(e)
        else:
            success_counter += 1

    message = f"Разблокировано {success_counter} пользователей"
    if error_counter > 0:
        message += f" {error_counter} - с ошибкой"

    messages.success(request, message)


unban_in_all_bots.short_description = "Unban: Разблокировать везде (боты + чаты)"


def ban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id):
    success_counter = 0
    error_counter = 0
    owned_bot = OwnedBot.objects.get(chat_id=bot_chat_id)
    for user in queryset:
        ban_url = owned_bot.get_ban_url(user.chat_id)
        response = requests.get(ban_url, headers=settings.HEADERS)
        status_code = json.loads(response.text).get("code")
        if status_code != 0:
            send_tg_message_to_admins_from_django(
                f"Проблема с блокировкой пользователя: chat_id {user.chat_id} в боте {owned_bot.name}\n\n"
                f"response: {response.text}"
            )
            logging.error(f"Something went wrong. Can't ban user {user.chat_id} in bot {owned_bot.name}\n\n"
                          f"response: {response.text}")
            error_counter += 1
        else:
            logging.error(f"User {user.chat_id} was banned in bot {owned_bot.name}")
            success_counter += 1

    message = f"Заблокировано {success_counter} пользователей в боте {owned_bot.name}"
    if error_counter > 0:
        message += f" {error_counter} - с ошибкой"

    messages.success(request, message)


def ban_in_beginner_bot(admin_model, request, queryset):
    ban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id=5794998235)


ban_in_beginner_bot.short_description = "Ban: Заблокировать в боте 'Зал для начинающих'"


def ban_in_rookie_bot(admin_model, request, queryset):
    ban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id=5885196609)


ban_in_rookie_bot.short_description = "Ban: Заблокировать в боте 'Тренировки с гантелями'"


def ban_in_advanced_bot(admin_model, request, queryset):
    ban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id=5995892505)


ban_in_advanced_bot.short_description = "Ban: Заблокировать в боте 'Зал для уверенных'"


def ban_in_bands_bot(admin_model, request, queryset):
    ban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id=6169093963)


ban_in_bands_bot.short_description = "Ban: Заблокировать в боте 'Тренировки с резинками'"


def unban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id):
    success_counter = 0
    error_counter = 0
    owned_bot = OwnedBot.objects.get(chat_id=bot_chat_id)
    for user in queryset:
        unban_url = owned_bot.get_unban_url(user.chat_id)
        response = requests.get(unban_url, headers=settings.HEADERS)
        status_code = json.loads(response.text).get("code")
        if status_code != 0:
            send_tg_message_to_admins_from_django(
                f"Проблема с разблокировкой пользователя: chat_id {user.chat_id} в боте {owned_bot.name}\n\n"
                f"response: {response.text}"
            )
            logging.error(f"Something went wrong. Can't unban user {user.chat_id} in bot {owned_bot.name}\n\n"
                          f"response: {response.text}")
            error_counter += 1
        else:
            logging.error(f"User {user.chat_id} was unbanned in bot {owned_bot.name}")
            success_counter += 1

    message = f"Разблокировано {success_counter} пользователей в боте {owned_bot.name}"
    if error_counter > 0:
        message += f" {error_counter} - с ошибкой"

    messages.success(request, message)


def unban_in_beginner_bot(admin_model, request, queryset):
    unban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id=5794998235)


unban_in_beginner_bot.short_description = "Unban: Разблокировать в боте 'Зал для начинающих'"


def unban_in_rookie_bot(admin_model, request, queryset):
    unban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id=5885196609)


unban_in_rookie_bot.short_description = "Unban: Разблокировать в боте 'Тренировки с гантелями'"


def unban_in_advanced_bot(admin_model, request, queryset):
    unban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id=5995892505)


unban_in_advanced_bot.short_description = "Unban: Разблокировать в боте 'Зал для уверенных'"


def unban_in_bands_bot(admin_model, request, queryset):
    unban_from_admin_in_target_bot(admin_model, request, queryset, bot_chat_id=6169093963)


unban_in_bands_bot.short_description = "Unban: Разблокировать в боте 'Тренировки с резинками'"
