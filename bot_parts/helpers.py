from datetime import datetime, timedelta

import telegram
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from telegram import Update
from telegram.ext import ContextTypes

from product.models import ProductsInMemory
from user.models import User


async def send_tg_message(
        context: ContextTypes.DEFAULT_TYPE,
        chat_id,
        message,
        parse_mode='HTML',
        update: Update = None,
        keyboard=None,
        delete_from=False
):
    """
        Send message from bot
    """
    try:
        await context.bot.send_message(
            chat_id,
            message,
            parse_mode,
            reply_markup=keyboard
        )
        if delete_from and update:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=update.effective_message.message_id
            )
    except (telegram.error.Forbidden, telegram.error.BadRequest):
        pass


def chat_is_private(update: ContextTypes.DEFAULT_TYPE) -> bool:
    """
        avoid not private messages (administered chats)
    """
    message = update.message if update.message else update.callback_query.message
    return message.chat.type == 'private'


async def check_bot_context(update, context, force_update: bool = False):
    """
        Add user and sub state in context
    """
    if not chat_is_private(update):
        return
    if not context.user_data.get('user') or force_update:
        user, _ = await User.objects.aget_or_create(
            chat_id=update.effective_chat.id,
            defaults={
                'username': update.effective_chat.username
            }
        )
        active_sub = (
            await user.subscriptions.select_related('product').order_by('-unsub_date').filter(is_active=True).afirst()
        )
        setattr(user, 'active_subscription', active_sub)
        if not active_sub:
            last_sub = (
                await user.subscriptions
                .select_related('product')
                .filter(unsub_date__gte=timezone.now() - timedelta(days=7), product__is_trial=False)
                .order_by('-unsub_date')
                .afirst()
            )
            setattr(user, 'last_sub', last_sub)
        context.user_data['user'] = user


def get_tariffs_text(user) -> str:
    """
        Машина фитнеса - 1 месяц, <s>2000</s> 1800 RUB
    """
    result = '\n\n'
    prep_text = (
        '{displayed_name} - {period_name}, <s>{crossed_out_price}</s> {payment_amount} {payment_currency}\n'
    )
    crossed_out_price = None
    for product in sorted(ProductsInMemory.trial_products, key=lambda x: x.amount):
        result += prep_text.format(
            displayed_name=product.displayed_name,
            period_name=product.payment_name,
            crossed_out_price='',
            payment_amount=product.amount,
            payment_currency=product.currency,
        )

    for product in sorted(ProductsInMemory.not_trial_products, key=lambda x: x.amount):
        if not crossed_out_price:
            crossed_out_price = product.amount
            result += prep_text.format(
                displayed_name=product.displayed_name,
                period_name=product.payment_name,
                crossed_out_price='',
                payment_amount=product.amount,
                payment_currency=product.currency,
            )
        else:
            result += prep_text.format(
                displayed_name=product.displayed_name,
                period_name=product.payment_name,
                payment_amount=product.amount,
                crossed_out_price=float(crossed_out_price) * product.sub_period,
                payment_currency=product.currency,
            )
    if user.last_sub is not None:
        product = user.last_sub.product
        result += "\n(доступно 7 дней!)\nВозобновление прошлой подписки по старой цене: \n" + prep_text.format(
                displayed_name=product.displayed_name,
                period_name=product.payment_name,
                payment_amount=user.last_sub.payment_amount,
                crossed_out_price='',
                payment_currency=user.last_sub.payment_currency,
            )

    return result


def get_beautiful_sub_date(first_sub_date: datetime) -> str | None:
    """
        Returns "2 часа 15 мин", example usage: "Ты с нами уже: ..."
    """
    current_date = timezone.now()
    date_diff = relativedelta(current_date, first_sub_date)
    time_units = {
        "years": ("год", "года", "лет"),
        "months": ("месяц", "месяца", "месяцев"),
        "days": ("день", "дня", "дней"),
        "hours": ("час", "часа", "часов"),
        "minutes": ("минуту", "минуты", "минут"),
    }

    res = ""
    for unit, (unit_singular, unit_plural_2_4, unit_plural_5plus) in time_units.items():
        value = getattr(date_diff, unit)
        if value:
            res += f"{value} "
            if value % 10 == 1 and value % 100 != 11:
                res += unit_singular
            elif 2 <= value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20):
                res += unit_plural_2_4
            else:
                res += unit_plural_5plus
            res += ", "

    res = res.rstrip(", ")
    if not res:
        res = 'Начало положено!'
    res += " 🏆"
    return res


async def send_message_to_admins_from_bot(bot_context, text):
    admins_chat_id = User.objects.filter(is_superuser=True).values_list('chat_id', flat=True)
    async for chat_id in admins_chat_id:
        await bot_context.bot.send_message(
            chat_id=chat_id,
            text=text,
        )
