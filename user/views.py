import asyncio

import aiohttp
import requests
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View

from product.models import SubPeriodTypes
from subscription.models import Subscription
from user.models import User
from utils.helpers import get_tg_payload


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
        users = self.get_users(to_users, user_pk)
        text = request.POST.get('message_text')
        tasks = []
        async with aiohttp.ClientSession() as session:
            async for user in users:
                payload = get_tg_payload(chat_id=user.chat_id, message_text=text)
                tasks.append(asyncio.create_task(self.send_message(session, payload)))

            await asyncio.gather(*tasks)
        report_mes = self.report_message.format(
            success_counter=self.success_counter,
            error_counter=self.error_counter,
            block_counter=self.block_counter
        )
        messages.add_message(request, messages.SUCCESS, report_mes)
        return redirect(self.return_url)

    async def send_message(self, session, payload):
        response = await session.post(
            settings.TG_SEND_MESSAGE_URL,
            json=payload
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
