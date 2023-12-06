import datetime
import json
import logging
from time import sleep

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from yookassa.domain.exceptions import BadRequestError

from bot_parts.models import ContentInMemory
from message_templates.models import MessageTemplatesInMemory
from payment.models import Payment, PaymentStatus, Refund
from product.models import Product, SubPeriodTypes
from subscription.models import Subscription
from utils.helpers import (
    get_tg_payload,
    send_tg_message_to_admins_from_django,
    get_tg_payload_with_callbacks,
    ban_user_in_owned_bots,
    unban_user_in_owned_bots
)
from utils.services import create_yoo_refund

logger = logging.getLogger(__name__)


class YooPaymentCallBackView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        request_data = json.loads(request.body.decode("utf-8"))
        returned_obj, event = request_data.get('object'), request_data.get('event')
        match event:
            case "refund.succeeded":
                try:
                    self.process_refund(returned_obj)
                except Refund.DoesNotExist:
                    logger.error(f'Problem with refund: {request_data}')
                    send_tg_message_to_admins_from_django(f"Не удалось провести возврат {request_data}")
                    return JsonResponse({"status": "success"})

            case "payment.succeeded" | "payment.canceled":
                # BAD CODE AREA :)
                counter = 0
                payment = None
                while counter < 5:  # TODO Fix fast response from yookassa.
                    counter += 1
                    try:
                        sleep(1)
                        payment = (
                            Payment.objects
                            .select_related('user', 'subscription')
                            .prefetch_related('user__subscriptions')
                            .get(
                                payment_service='YooKassa',
                                payment_service_id=str(returned_obj.get('id')),
                                status=PaymentStatus.PENDING,
                            )
                        )
                    except Payment.DoesNotExist:
                        pass
                if not payment:
                    logger.error(f'Платеж не найден {returned_obj}')
                    return JsonResponse({"status": "success"})
                # END BAD CODE AREA
                if event == "payment.succeeded":
                    self.process_payment_success(
                        payment=payment,
                        returned_obj=returned_obj,
                    )
                else:
                    self.process_payment_canceled(payment, returned_obj=returned_obj)

        return JsonResponse({"status": "success"})

    def process_payment_success(self, payment, returned_obj):
        payment.status = PaymentStatus.SUCCEEDED
        metadata = returned_obj.get('metadata')
        is_auto_payment = metadata['auto_payment'] == "true"
        product = Product.objects.get(pk=metadata.get('product_id'))
        if is_auto_payment:
            subscription = Subscription.objects.get(
                is_active=True,
                user=payment.user,
                product=product
            )
        else:
            subscription = Subscription.objects.create(
                is_active=True,
                user=payment.user,
                product=product,
                payment_amount=payment.amount,
                payment_currency=payment.currency,
            )
        match product.sub_period_type:
            case SubPeriodTypes.month:
                subscription.unsub_date = datetime.datetime.now() + relativedelta(months=product.sub_period)
            case SubPeriodTypes.day:
                subscription.unsub_date = datetime.datetime.now() + relativedelta(days=product.sub_period)

        if is_auto_payment:
            default = "Подписка на {payment_name} фитнеса успешно продлена \uD83D\uDCAA"
            text = MessageTemplatesInMemory.get('auto_payment_success', default=default).format(
                payment_name=product.payment_name,
            )
            payload = get_tg_payload(subscription.user.chat_id, text)

        else:
            subscription.verified_payment_id = returned_obj.get('payment_method', {}).get('id', None)
            payment.subscription = subscription
            if not subscription.user.first_sub_date:
                subscription.user.first_sub_date = datetime.datetime.now()
            subscription.user.save()
            payment.subscription.save()
            default = (
                    "Платеж на сумму {value} {currency} совершен успешно.\n"
                    "Оформлена подписка на {sub_period}\n\n"
                    "Спасибо за доверие ❤\nВыбери, с чего хочешь начать!"
                )
            text = MessageTemplatesInMemory.get('payment_success', default=default).format(
                    value=payment.amount,
                    currency=payment.currency,
                    sub_period=product.payment_name
                )
            buttons = []
            for content in ContentInMemory.content():
                buttons.append(
                    {content.name: content.link}
                )
            payload = get_tg_payload(subscription.user.chat_id, text, buttons)

        subscription.save()
        payment.save()
        self.send_tg_message(payload)
        unban_user_in_owned_bots(payment.user.chat_id)

    def process_payment_canceled(self, payment, returned_obj):
        payment.status = PaymentStatus.CANCELED
        is_auto_payment = returned_obj.get('metadata', {}).get('auto_payment') == "true"
        payment.cancelled()
        payment.save()
        if is_auto_payment:
            default = (
                    "Упс, что-то пошло не так!\nМы не смогли продлить твою подписку в клубе. Возможно, "
                    "на карте не хватает средств.\nПопробуй продлить подписку самостоятельно \uD83D\uDC47"
                )
            text = MessageTemplatesInMemory.get('auto_payment_error', default=default)
            ban_user_in_owned_bots(payment.user.chat_id)
        else:
            if payment.user.subscriptions.filter(is_active=True).exists():
                return
            default = (
                    "Упс, что-то пошло не так!\n"
                    "Не получилось создать твою подписку в клуб. Попробуй оплатить через 5-10 минут.\n"
                    "Если все еще не получится - пиши мне в личку @snackiebird1"
                )
            text = MessageTemplatesInMemory.get('payment_error', default=default)

        payment.user.state = 'TARIFF_CHOICE'
        payment.user.save()
        buttons = []
        for product in Product.objects.filter(is_active=True).order_by('amount'):
            buttons.append({
                f"{product.payment_name}, {product.amount} {product.currency}": product.pk
            })
        payload = get_tg_payload_with_callbacks(chat_id=payment.user.chat_id, message_text=text, buttons=buttons)
        self.send_tg_message(payload)

    def process_refund(self, returned_obj):
        refund_id = returned_obj.get('id')
        payment_service_id = returned_obj.get('payment_id')
        refund = (
            Refund.objects
            .select_related('payment', 'payment__subscription', 'payment__subscription__product', 'payment__user')
            .get(payment_service_id=refund_id, payment__payment_service_id=payment_service_id)
        )
        text = f"Возврат суммы {refund.payment.amount} {refund.payment.currency} проведен успешно.\n"

        refund.success()

        text += f"Подписка на клуб завершена."

        payload = get_tg_payload(chat_id=refund.payment.user.chat_id, message_text=text)
        self.send_tg_message(payload)

        admins_text = (f"Возврат суммы {refund.payment.amount} {refund.payment.currency} для пользователя "
                       f"@{refund.payment.user.username} проведен успешно.\n")
        send_tg_message_to_admins_from_django(admins_text)
        ban_user_in_owned_bots(refund.payment.user.chat_id)

    @staticmethod
    def send_tg_message(payload):
        response = requests.post(settings.TG_SEND_MESSAGE_URL, json=payload)
        if response.status_code != 200:
            logger.error(f'Не удалось отправить сообщение: {payload}')


class RefundCreateView(View):
    return_url = '/payment/payment/'
    error_message = 'Что-то пошло не так. Попробуйте перезагрузить страницу и повторите попытку'
    refund_already_exist_message = 'Возврат уже был создан ранее. Обратитесь в YooKassa за уточнением'
    success_message = 'Возврат успешно создан'

    def post(self, request, **kwargs):
        payment_id = request.POST.get('payment_id')
        try:
            if payment_id and request.user.is_superuser:
                db_payment = Payment.objects.get(pk=payment_id)
            else:
                raise Payment.DoesNotExist
        except Payment.DoesNotExist:
            messages.add_message(request, messages.ERROR, self.error_message)
            return redirect(self.return_url)

        try:
            yoo_refund = create_yoo_refund(payment=db_payment)
        except BadRequestError:
            db_payment.is_refunded = True
            db_payment.save()
            messages.add_message(request, messages.WARNING, self.refund_already_exist_message)
            return redirect(self.return_url)

        Refund.objects.create(
            payment=db_payment,
            payment_service_id=yoo_refund.get('id')
        )
        messages.add_message(request, messages.SUCCESS, self.success_message)
        return redirect(self.return_url)
