import datetime

from django.db import models

from subscription.models import Subscription
from user.models import NOT_NULLABLE, NULLABLE, User
from utils.models import PaymentCurrency


class PaymentStatus(models.TextChoices):
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    CANCELED = 'canceled'
    REFUNDED = 'refunded'


class Payment(models.Model):
    status = models.CharField(
        verbose_name='Статус платежа',
        max_length=128,
        choices=PaymentStatus.choices,
        **NOT_NULLABLE
    )
    payment_service_id = models.UUIDField(
        verbose_name='Id платежа в платежной системе',
        **NOT_NULLABLE,
        unique=False
    )
    payment_service = models.CharField(
        verbose_name='Платежная система',
        **NOT_NULLABLE,
        max_length=128,
        default='YooKassa'
    )
    amount = models.FloatField(verbose_name='Сумма платежа', **NOT_NULLABLE)
    currency = models.CharField(
        verbose_name='Валюта платежа',
        max_length=128,
        choices=PaymentCurrency.choices,
        default=PaymentCurrency.RUB,
        **NOT_NULLABLE,
    )
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='payments',
        on_delete=models.DO_NOTHING
    )

    subscription = models.ForeignKey(
        Subscription,
        verbose_name='Подписка',
        related_name='payments',
        on_delete=models.DO_NOTHING,
        **NULLABLE
    )

    is_refunded = models.BooleanField(verbose_name='Возвращен?', default=False)

    async def cancelled(self):
        if self.subscription:
            self.subscription.is_auto_renew = False
            self.subscription.is_active = False
            await self.subscription.asave()

    def __str__(self):
        return f"{self.id}: {self.amount} from {self.user}"

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'


class RefundStatus(models.TextChoices):
    CREATED = 'created'
    SUCCEEDED = 'succeeded'


class Refund(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, verbose_name='Возврат', related_name='refund')
    status = models.CharField(
        choices=RefundStatus.choices,
        verbose_name='Статус',
        default=RefundStatus.CREATED,
        max_length=128
    )
    payment_service_id = models.UUIDField(
        verbose_name='Id возврата в платежной системе',
        **NOT_NULLABLE,
        unique=False
    )
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)

    async def success(self):
        self.payment.subscription.is_active = False
        self.payment.subscription.is_auto_renew = False
        self.payment.subscription.unsub_date = datetime.datetime.now()
        await self.payment.subscription.asave()
        self.payment.is_refunded = True
        self.payment.status = PaymentStatus.REFUNDED
        await self.payment.asave()
        self.status = RefundStatus.SUCCEEDED
        await self.asave()

    def __str__(self):
        return f"Refund for payment {self.payment.id}"

    class Meta:
        verbose_name = 'Возврат'
        verbose_name_plural = 'Возвраты'
