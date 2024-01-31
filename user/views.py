import asyncio
import json

import aiohttp
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View

from product.models import SubPeriodTypes, Product
from subscription.models import Subscription
from user.models import User
from utils.helpers import get_tg_payload, get_tg_payload_with_callbacks


class SendMessageView(View):
    return_url = '/user/user/'
    report_message = (
        '{success_counter} сообщений отправлено успешно. '
        '{error_counter} - не отправлены. '
        '{block_counter} - бот заблокирован.'
    )
    error_counter = 0
    block_counter = 0
    success_counter = 0

    async def post(self, request, **kwargs):
        to_users = request.POST.get('to_users')
        user_pk = request.POST.get('user_id')
        text = request.POST.get('message_text')
        with_keyboard = to_users == "all_unsub" and request.POST.get("with_keyboard") == "true"
        users = self.get_users(to_users, user_pk)
        image_file = request.FILES.get('image')
        if image_file:
            image_file = image_file.read()
        buttons = []
        if with_keyboard:
            async for product in Product.objects.filter(is_active=True).order_by('amount'):
                buttons.append({f"{product.payment_name}, {product.amount} {product.currency}": product.pk})

        tasks = []
        async with aiohttp.ClientSession() as session:
            async for user in users:
                if with_keyboard:
                    user.state = "TARIFF_CHOICE"
                    payload = get_tg_payload_with_callbacks(chat_id=user.chat_id,
                                                            message_text=text,
                                                            buttons=buttons)
                else:
                    payload = get_tg_payload(chat_id=user.chat_id, message_text=text)

                if image_file:
                    form = aiohttp.FormData()
                    form.add_field('photo', image_file, filename='photo.jpg', content_type='image/jpeg')
                    form.add_field('caption', text)
                    form.add_field('text', text)
                    form.add_field('chat_id', str(user.chat_id))
                    if with_keyboard:
                        form.add_field('reply_markup',
                                       json.dumps(payload["reply_markup"]),
                                       content_type="application/json")
                    task = self.send_photo(session, form=form)
                else:
                    task = self.send_message(session, payload=payload)
                tasks.append(asyncio.create_task(task))

            await asyncio.gather(*tasks)
        report_mes = self.report_message.format(
            success_counter=self.success_counter,
            error_counter=self.error_counter,
            block_counter=self.block_counter
        )
        messages.add_message(request, messages.SUCCESS, report_mes)
        await User.objects.abulk_update(users, ['state'])
        return redirect(self.return_url)

    async def send_photo(self, session, form):
        response = await session.post(
            settings.TG_SEND_PHOTO_URL,
            data=form,
        )
        if response.status == 200:
            self.success_counter += 1
        elif response.status == 403:
            self.block_counter += 1
        else:
            self.error_counter += 1

    async def send_message(self, session, payload):
        response = await session.post(
            settings.TG_SEND_MESSAGE_URL,
            json=payload,
        )
        if response.status == 200:
            self.success_counter += 1
        elif response.status == 403:
            self.block_counter += 1
        else:
            self.error_counter += 1

    @staticmethod
    def get_users(field_value, pk=None):
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
