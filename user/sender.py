import asyncio
import json
import logging
from asyncio import Task
from typing import TextIO, Coroutine

import aiohttp
from django.conf import settings
from django.db.models import QuerySet

from product.models import SubPeriodTypes, Product
from subscription.models import Subscription
from user.helper import CustomCounter
from user.models import User
from utils.helpers import get_tg_payload_with_callbacks, get_tg_payload

CHUNK_SIZE = 30
logger = logging.getLogger(__name__)


class UserSender:
    @classmethod
    async def send_to_user(cls, to_user: str,
                           user_pk: int,
                           message_text: str,
                           with_keyboard: bool = False,
                           image_io: TextIO | None = None):
        users: QuerySet[User] = cls.get_users(to_user, user_pk)
        counter = CustomCounter()
        buttons: list[dict] = []
        if with_keyboard:
            buttons = await cls.get_keyboard_buttons()
        tasks: list[Coroutine] = []
        async for user in users:
            payload = await cls.get_payload(with_keyboard, message_text, user, buttons)
            task = cls.send_message_or_photo(payload, image_io, message_text, counter)
            tasks.append(task)

        await cls.run_tasks_chunked(tasks)

        if with_keyboard:
            await cls.update_users_state(users)

        await cls.send_report_message(counter.report_message)

    @staticmethod
    async def run_tasks_chunked(tasks: list[Coroutine], chunk_size: int = CHUNK_SIZE):
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            await asyncio.gather(*chunk)
            await asyncio.sleep(1)

    @staticmethod
    async def get_payload(with_keyboard: bool, message_text: str, user: User, buttons: list[dict] | None) -> dict:
        if with_keyboard:
            user.state = "TARIFF_CHOICE"
            return get_tg_payload_with_callbacks(chat_id=user.chat_id,
                                                 message_text=message_text,
                                                 buttons=buttons)
        else:
            return get_tg_payload(chat_id=user.chat_id, message_text=message_text)

    @classmethod
    async def send_message_or_photo(cls, payload: dict, image_io: TextIO | None, message_text: str, counter: CustomCounter) -> Task:
        if image_io:
            form = cls.prepare_photo_form(payload, message_text, image_io)
            return asyncio.create_task(cls.send_photo(form, counter))
        else:
            return asyncio.create_task(cls.send_message(payload, counter))

    @staticmethod
    def prepare_photo_form(payload: dict, message_text: str, image_io: TextIO) -> aiohttp.FormData:
        form = aiohttp.FormData()
        form.add_field('photo', image_io, filename='photo.jpg', content_type='image/jpeg')
        form.add_field('caption', message_text)
        form.add_field('chat_id', str(payload["chat_id"]))
        if "reply_markup" in payload:
            form.add_field('reply_markup',
                           json.dumps(payload["reply_markup"]),
                           content_type="application/json")
        return form

    @staticmethod
    async def get_keyboard_buttons() -> list[dict]:
        buttons = []
        async for product in Product.objects.filter(is_active=True).order_by('amount'):
            buttons.append({f"{product.payment_name}, {product.amount} {product.currency}": product.pk})
        return buttons

    @classmethod
    async def send_photo(cls, form: aiohttp.FormData, counter: CustomCounter):
        async with aiohttp.ClientSession() as session:
            response = await session.post(settings.TG_SEND_PHOTO_URL, data=form)
            cls.handle_response(response, counter)

    @classmethod
    async def send_message(cls, payload: dict, counter: CustomCounter):
        async with aiohttp.ClientSession() as session:
            response = await session.post(settings.TG_SEND_MESSAGE_URL, json=payload)
            cls.handle_response(response, counter)

    @staticmethod
    def handle_response(response: aiohttp.ClientResponse, counter: CustomCounter):
        if response.status == 200:
            counter.success_counter += 1
        elif response.status == 403:
            counter.block_counter += 1
        else:
            counter.error_counter += 1

    @staticmethod
    def get_users(field_value: str, pk=None) -> QuerySet[User] | list:
        match field_value:
            case 'current':
                return User.objects.filter(pk=pk)
            case 'all_unsub':
                user_ids = (
                    Subscription.objects
                    .select_related('product')
                    .filter(is_active=True)
                    .values_list('user_id', flat=True)
                    .distinct()
                )
                return User.objects.exclude(pk__in=user_ids)
            case 'all_subs':
                user_ids = (
                    Subscription.objects
                    .select_related('product')
                    .filter(is_active=True)
                    .values_list('user_id', flat=True)
                    .distinct()
                )
                return User.objects.filter(pk__in=user_ids)
            case 'one_month':
                user_ids = (
                    Subscription.objects
                    .select_related('product')
                    .filter(
                        is_active=True,
                        product__sub_period=1,
                        product__sub_period_type=SubPeriodTypes.month
                    )
                    .values_list('user_id', flat=True)
                    .distinct()
                )
                return User.objects.filter(pk__in=user_ids)
            case 'three_month':
                user_ids = (
                    Subscription.objects
                    .select_related('product')
                    .filter(
                        is_active=True,
                        product__sub_period=3,
                        product__sub_period_type=SubPeriodTypes.month
                    )
                    .values_list('user_id', flat=True)
                    .distinct()
                )
                return User.objects.filter(pk__in=user_ids)
            case 'one_year':
                user_ids = (
                    Subscription.objects
                    .select_related('product')
                    .filter(
                        is_active=True,
                        product__sub_period=12,
                        product__sub_period_type=SubPeriodTypes.month
                    )
                    .values_list('user_id', flat=True)
                    .distinct()
                )
                return User.objects.filter(pk__in=user_ids)
            case 'trial':
                user_ids = (
                    Subscription.objects
                    .select_related('product')
                    .filter(
                        is_active=True,
                        product__is_trial=True
                    )
                    .values_list('user_id', flat=True)
                    .distinct()
                )
                return User.objects.filter(pk__in=user_ids)
            case 'all':
                return User.objects.all()
            case _:
                return []

    @staticmethod
    async def send_report_message(message_text: str):
        async with aiohttp.ClientSession() as session:
            async for chat_id in User.objects.filter(is_superuser=True).values_list('chat_id', flat=True):
                payload = get_tg_payload(chat_id=chat_id, message_text=message_text)
                response = await session.post(settings.TG_SEND_MESSAGE_URL, json=payload)
                if response.status != 200:
                    logger.error(f'Не удалось отправить сообщение: {payload}\n{response.text}')

    @staticmethod
    async def update_users_state(users: QuerySet[User]):
        await User.objects.abulk_update(users, ['state'])

    @classmethod
    def report_message(cls):
        return cls._report_message.format(
            success_counter=cls.success_counter,
            error_counter=cls.error_counter,
            block_counter=cls.block_counter
        )
