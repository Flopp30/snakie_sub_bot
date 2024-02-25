import asyncio
import json
import logging
from datetime import datetime, timedelta

import aiohttp
from django.conf import settings
from django.db.models import Q
from telegram.ext import CallbackContext

from bot_parts.helpers import send_message_to_admins_from_bot, send_tg_message
from bot_parts.keyboards import get_tariff_board
from bot_parts.models import OwnedChat, SalesInMemory, ContentInMemory, OwnedBotsInMemory, OwnedChatInMemory
from message_templates.models import MessageTemplatesInMemory
from payment.models import Payment, PaymentStatus
from product.models import ProductsInMemory
from subscription.models import Subscription
from user.models import User
from utils.services import create_yoo_auto_payment

logger = logging.getLogger(__name__)


async def reload_in_memory_data(*args, **kwargs):
    await ProductsInMemory.load_products()
    await MessageTemplatesInMemory.load_templates()
    await SalesInMemory.update_sales_is_available()
    await ContentInMemory.aload_contents()
    await OwnedBotsInMemory.areload_bots()
    await OwnedChatInMemory.areload_chats()


async def renew_sub_hourly(context: CallbackContext):
    now = datetime.now()
    expired_subs = Subscription.objects.select_related('product', 'user').filter(unsub_date__lte=now, is_active=True)
    unsub_users = []
    inactivated_subs = []
    async for sub in expired_subs:
        if sub.is_auto_renew and sub.verified_payment_id:
            metadata = {
                'product_id': sub.product.id
            }
            yoo_payment = create_yoo_auto_payment(sub=sub, product=sub.product, metadata=metadata)
            await Payment.objects.acreate(
                status=PaymentStatus.PENDING,
                payment_service_id=yoo_payment.get('id'),
                amount=yoo_payment.get('amount').get('value'),
                currency=yoo_payment.get('amount').get('currency'),
                user=sub.user,
                subscription=sub
            )
        else:
            sub.is_active = False
            sub.is_auto_renew = False
            inactivated_subs.append(sub)

            sub.user.state = 'TARIFF_CHOICE'
            unsub_users.append(sub.user)
            await ban_user_in_owned_bots(sub.user.chat_id, bot_context=context)
            if sub.product.is_trial:
                key = 'trail_ended'
            else:
                key = 'not_auto_renew'

            default = (
                "Твоя подписка на клуб закончилась. Ты можешь продлить её самостоятельно, выбрав подходящий тариф"
            )
            mes_text = await MessageTemplatesInMemory.aget(key, default=default)
            await send_tg_message(
                chat_id=sub.user.chat_id,
                message=mes_text,
                keyboard=get_tariff_board(user=sub.user, sub=sub),
                context=context
            )

    if inactivated_subs:
        await Subscription.objects.abulk_update(inactivated_subs, ['is_active', 'is_auto_renew'])
    if unsub_users:
        await User.objects.abulk_update(unsub_users, ['state'])


async def ban_user_in_owned_bots(user_chat_id, bot_context):
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
                await send_message_to_admins_from_bot(
                    bot_context,
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
            task = asyncio.create_task(kick_chat_member(chat, aio_session, user_chat_id, bot_context))
            tasks.append(task)
        await asyncio.gather(*tasks)


async def kick_chat_member(chat: OwnedChat, aio_session, user_chat_id, bot_context):
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
        await send_message_to_admins_from_bot(
            bot_context,
            f"Проблема с киком пользователя: chat_id {user_chat_id} в чате {chat.name}\n\n"
            f"response: {await response.text()}\n"
        )


async def send_reminders_notification(context: CallbackContext):
    """
        If the user's last activity was during the target period and he does not have an active subscription -
        send a message
    """
    await SalesInMemory.update_sales_is_available()
    if not SalesInMemory.is_available:
        return
    now = datetime.now()
    tariff_board = get_tariff_board()
    one_day_users = User.objects.prefetch_related('subscriptions').filter(
        Q(last_visit_time__gte=(now - timedelta(days=1))) &
        Q(last_visit_time__lte=(now - timedelta(hours=23)))
    ).exclude(subscriptions__is_active=True)
    five_day_users = User.objects.prefetch_related('subscriptions').filter(
        Q(last_visit_time__gte=(now - timedelta(days=5))) &
        Q(last_visit_time__lte=(now - timedelta(days=4, hours=23)))
    ).exclude(subscriptions__is_active=True)
    updated_users = []
    async for user in one_day_users:
        if user.chat_id > 0:
            await send_tg_message(
                chat_id=user.chat_id,
                message=await MessageTemplatesInMemory.aget('text_one_day_notification'),
                keyboard=tariff_board,
                context=context
            )
            user.state = 'TARIFF_CHOICE'
            updated_users.append(user)
    async for user in five_day_users:
        if user.chat_id > 0:
            await send_tg_message(
                chat_id=user.chat_id,
                message=await MessageTemplatesInMemory.aget('text_five_day_notification'),
                keyboard=tariff_board,
                context=context
            )
            user.state = 'TARIFF_CHOICE'
            updated_users.append(user)
    await User.objects.abulk_update(updated_users, ('state', ))
