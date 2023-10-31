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

    def post(self, request, **kwargs):
        to_users = request.POST.get('to_users')
        user_pk = request.POST.get('user_id')
        error_counter, success_counter, block_counter = 0, 0, 0
        users = self.get_users(to_users, user_pk)
        text = request.POST.get('message_text')
        for user in users:
            payload = get_tg_payload(chat_id=user.chat_id, message_text=text)
            response = requests.post(settings.TG_SEND_MESSAGE_URL, json=payload)
            if response.status_code == 200:
                success_counter += 1
            elif response.status_code == 403:
                block_counter += 1
            else:
                error_counter += 1
        report_mes = self.report_message.format(
            success_counter=success_counter,
            error_counter=error_counter,
            block_counter=block_counter
        )
        messages.add_message(request, messages.SUCCESS, report_mes)
        return redirect(self.return_url)

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
