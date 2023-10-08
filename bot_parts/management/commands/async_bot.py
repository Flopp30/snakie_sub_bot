import logging
from datetime import timedelta
from textwrap import dedent

from django.conf import settings
from django.core.management import BaseCommand
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)

from bot_parts.helpers import check_bot_context
from message_templates.models import MessageTemplates

logger = logging.getLogger('tbot')


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await check_bot_context(update, context)
    # if context.user_data['user'].state != 'NEW':
    #     return await welcome_letter(update, context)
    text = dedent(f"""
        Привет ✨
        Это бот блогерки @snackiebird1. <b>SnakieBot</b>
        Нажми /start , чтобы начать
    """)
    await context.bot.send_message(
        chat_id,
        text=text,
        parse_mode='HTML',
    )
    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.effective_message.message_id
    )
    context.user_data['user'].state = 'START'
    return 'START'


async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    if update.message:
        user_reply = update.message.text
    elif update.callback_query.data:
        user_reply = update.callback_query.data
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = context.user_data['user'].state or 'START'
    states_function = {
        'NEW': start,
        # 'START': start,
        # 'START_AFTER_CLUB_PAYMENT': start,
        # 'START_AFTER_GROUP_LESSONS': start,
        # 'WELCOME_CHOICE': handle_welcome_choice,
        # 'SPEAK_CLUB_LEVEL_CHOICE': handle_speak_club_level_choice,
        # 'LOWER_LEVEL_CHOICE': handle_lower_level_choice,
        # 'AWAIT_LEVEL_TEST_CONFIRMATION': handle_level_test_confirmation,
        # 'TEACHER_PAGINATION': teacher_pagination,
        # 'AWAIT_SUBSCRIPTION_ACTION': handle_subscription_action,
        # 'USER_SUBSCRIPTIONS_CHOICE': handle_user_subscriptions_choice,
        # 'AWAIT_REMINDER_CHOICE': handle_reminder_choice,
    }

    state_handler = states_function[user_state]
    next_state = await state_handler(update, context)
    context.user_data['user'].state = next_state
    await context.user_data['user'].asave()


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
    job_queue.run_repeating(MessageTemplates.load_templates,
                            interval=timedelta(minutes=10), first=3)

    application.add_handler(CallbackQueryHandler(user_input_handler))
    application.add_handler(MessageHandler(filters.TEXT, user_input_handler))
    application.add_handler(CommandHandler('start', user_input_handler))

    try:
        if settings.BOT_MODE == 'webhook':
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
