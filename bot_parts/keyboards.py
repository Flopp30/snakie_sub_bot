from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot_parts.models import ContentInMemory
from product.models import ProductsInMemory

START_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Хочу в клуб!', callback_data='in_club')]
    ]
)

UNSUB_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Да, хочу отписаться', callback_data='unsub_confirmed')],
        [InlineKeyboardButton('Нет, я машина для фитнеса!', callback_data='unsub_declined')]
    ]
)


def get_tariff_board(user=None, sub=None):
    if sub is None and user and user.last_sub:
        sub = user.last_sub
    buttons = []
    if sub:
        text = (
            f"Возобновление {sub.product.payment_name}, "
            f"{sub.payment_amount} {sub.payment_currency}"
        )
        buttons.append(
            [
                InlineKeyboardButton(text, callback_data="last_sub")
            ]
        )
        for product in sorted(ProductsInMemory.products_by_id.values(), key=lambda x: x.amount):
            if (product.amount != sub.payment_amount
                    and product.payment_name != sub.product.payment_name):
                text = f"{product.payment_name}, {product.amount} {product.currency}"
                buttons.append(
                    [
                        InlineKeyboardButton(text, callback_data=product.pk)
                    ]
                )
    else:
        for product in sorted(ProductsInMemory.products_by_id.values(), key=lambda x: x.amount):
            text = f"{product.payment_name}, {product.amount} {product.currency}"
            buttons.append(
                [
                    InlineKeyboardButton(text, callback_data=product.pk)
                ]
            )
    return InlineKeyboardMarkup(buttons)


def get_payment_board(button_text, payment_url):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(button_text, web_app=WebAppInfo(url=payment_url))]
        ]
    )


async def get_content_board():
    buttons = []
    contents = await ContentInMemory.acontent()
    for content in contents:
        buttons.append(
            [InlineKeyboardButton(content.name, url=content.link)]
        )
    return InlineKeyboardMarkup(buttons)
