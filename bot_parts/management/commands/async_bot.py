import logging
from datetime import timedelta

import telegram
from django.conf import settings
from django.core.management import BaseCommand
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
    PrefixHandler
)

from bot_parts.helpers import check_bot_context, get_tariffs_text, chat_is_private, get_beautiful_sub_date, \
    send_tg_message
from bot_parts.keyboards import START_BOARD, get_tariff_board, get_payment_board, UNSUB_BOARD, get_content_board
from bot_parts.models import SalesInMemory, ContentInMemory, OwnedBotsInMemory, OwnedChatInMemory
from message_templates.models import MessageTemplatesInMemory
from product.models import ProductsInMemory
from bot_parts.periodic_tasks import renew_sub_hourly, reload_in_memory_data, send_reminders_notification
from utils.services import create_payment

logger = logging.getLogger('tbot')


def sales_is_available(user):
    return SalesInMemory.is_available or bool(user.first_sub_date)


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()


async def help_(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    text = (await MessageTemplatesInMemory.aget('help')).format(user_id=context.user_data['user'].chat_id)
    await send_tg_message(
        chat_id=update.effective_chat.id,
        context=context,
        message=text,
        update=update,
        delete_from=True
    )
    context.user_data['user'].state = 'START'
    return 'START'


async def start(update, context):
    await check_bot_context(update, context, force_update=True)
    user = context.user_data['user']
    keyboard = None
    if user.active_subscription:
        keyboard = await get_content_board()
        mes_text = (await MessageTemplatesInMemory.aget('start_is_active')).format(
            first_sub_date=user.first_sub_date.strftime("%d.%m.%Y"),
            product_displayed_name=user.active_subscription.product.displayed_name,
            unsub_date=user.active_subscription.unsub_date.strftime("%d.%m.%Y"),
            sub_date_text=get_beautiful_sub_date(user.first_sub_date)
        )
        STATE = 'START'
    elif not sales_is_available(user):
        mes_text = await MessageTemplatesInMemory.aget('no_sale')
        STATE = 'START'
    else:
        mes_text = await MessageTemplatesInMemory.aget('start')
        keyboard = START_BOARD
        STATE = 'WELCOME_CHOICE'

    await send_tg_message(
        chat_id=update.effective_chat.id,
        context=context,
        message=mes_text,
        keyboard=keyboard,
        update=update,
        delete_from=True
    )
    context.user_data['user'].state = STATE
    return STATE


async def handle_welcome_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    if not update.callback_query:
        return 'WELCOME_CHOICE'
    text = (await MessageTemplatesInMemory.aget('tariffs')) + get_tariffs_text()
    await send_tg_message(
        chat_id=update.effective_chat.id,
        context=context,
        message=text,
        keyboard=get_tariff_board()
    )
    context.user_data['user'].state = 'TARIFF_CHOICE'
    return 'TARIFF_CHOICE'


async def handle_tariffs_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.callback_query.data:
        return 'TARIFF_CHOICE'
    await check_bot_context(update, context)
    product = await ProductsInMemory.get(int(update.callback_query.data))
    payment_url = await create_payment(product, context.user_data['user'])

    mes_text = (
        await MessageTemplatesInMemory.aget('text_with_payload_link', default='У тебя есть {time} для оплаты')
    ).format(time=settings.PAYMENT_LINK_TTL)
    keyboard = get_payment_board(
        button_text=f'Оплатить {product.amount} {product.currency}',
        payment_url=payment_url
    )
    await send_tg_message(
        chat_id=update.effective_chat.id,
        context=context,
        message=mes_text,
        keyboard=keyboard
    )
    return 'START'


async def unsubscribe_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    active_sub = context.user_data['user'].active_subscription
    if not active_sub:
        await send_tg_message(
            chat_id=update.effective_chat.id,
            context=context,
            message='У тебя нет активных подписок',
        )
        return 'START'

    if not active_sub.is_auto_renew:
        await send_tg_message(
            chat_id=update.effective_chat.id,
            context=context,
            message=(f'Текущая подписка завершится {active_sub.unsub_date.strftime("%d.%m.%Y")}'
                     ' и автоматически продлеваться не будет'),
        )
        return 'START'
    mes_text = (
        await MessageTemplatesInMemory.aget('unsub_confirmation', default='{unsub_date} - дата окончания подписки')
    ).format(unsub_date=active_sub.unsub_date.strftime('%d.%m.%Y'))

    await send_tg_message(
        chat_id=update.effective_chat.id,
        context=context,
        message=mes_text,
        keyboard=UNSUB_BOARD
    )
    return 'UNSUB_CHOICE'


async def handle_unsub_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    if update.callback_query.data == 'unsub_confirmed':
        active_sub = context.user_data['user'].active_subscription
        active_sub.is_auto_renew = False
        await active_sub.asave()
    mes_text = await MessageTemplatesInMemory.aget(update.callback_query.data)
    if mes_text:
        await send_tg_message(
            chat_id=update.effective_chat.id,
            context=context,
            message=mes_text
        )
    return 'START'


async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if chat_is_private(update):
        await check_bot_context(update, context)
        if update.message:
            user_reply = update.message.text
        elif update.callback_query.data:
            user_reply = update.callback_query.data
        else:
            return
        if user_reply.lower() == 'отписаться':
            user_state = 'UNSUB_START'
        elif user_reply == '/start' or not sales_is_available(context.user_data['user']):
            user_state = 'START'
        elif user_reply.lower() == '/help':
            user_state = 'HELP'
        else:
            user_state = context.user_data['user'].state or 'START'
        states_function = {
            'START': start,
            'NEW': start,
            'HELP': help_,
            'WELCOME_CHOICE': handle_welcome_choice,
            'TARIFF_CHOICE': handle_tariffs_choice,
            'UNSUB_START': unsubscribe_start,
            'UNSUB_CHOICE': handle_unsub_choice,
        }

        state_handler = states_function[user_state]
        next_state = await state_handler(update, context)
        context.user_data['user'].state = next_state
        await context.user_data['user'].asave()


async def reload_from_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if chat_is_private(update):
        await check_bot_context(update, context)
        if context.user_data['user'].is_superuser:
            await reload_in_memory_data()
            await send_tg_message(
                chat_id=update.effective_chat.id,
                context=context,
                message='Продукты, сообщения и даты продаж обновлены успешно'
            )


def main():
    import tracemalloc
    tracemalloc.start()
    # logger
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(settings.LOG_LEVEL)
    logger.addHandler(stream_handler)

    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    # periodic tasks
    job_queue = application.job_queue
    job_queue.run_repeating(
        reload_in_memory_data,
        interval=timedelta(minutes=10),
        first=1
    )
    job_queue.run_repeating(
        renew_sub_hourly,
        interval=timedelta(hours=1),
        first=5
    )
    # TODO remove later
    # job_queue.run_repeating(
    #     send_reminders_notification,
    #     interval=timedelta(hours=1),
    #     first=10
    # )

    application.add_handler(PrefixHandler(
        '!', ['reload_data'], reload_from_db))
    application.add_handler(CommandHandler('start', user_input_handler))
    application.add_handler(CommandHandler('help', user_input_handler))
    application.add_handler(CallbackQueryHandler(user_input_handler))
    application.add_handler(MessageHandler(filters.TEXT, user_input_handler))

    try:
        if settings.BOT_MODE == 'webhook':  # unused, may be required in future
            logger.warning('Bot started in WEBHOOK mode')
            application.run_webhook(
                listen="0.0.0.0",
                port=5000,
                url_path=settings.TELEGRAM_TOKEN,
                webhook_url=f"{settings.WEBHOOK_URL}{settings.TELEGRAM_TOKEN}"
            )
        else:
            logger.warning('Bot started in POLLING mode')
            application.run_polling()
    except Exception:
        import traceback
        logger.warning(traceback.format_exc())
