from django.db import models

from product.models import Product
from user.models import NOT_NULLABLE, NULLABLE, User
from utils.models import PaymentCurrency


class Subscription(models.Model):
    start_date = models.DateTimeField(verbose_name='Дата начала подписки', auto_now_add=True)
    unsub_date = models.DateTimeField(verbose_name='Дата окончания подписки', **NULLABLE)
    is_active = models.BooleanField(
        verbose_name='Активна?',
        default=True,
        **NOT_NULLABLE
    )
    is_auto_renew = models.BooleanField(
        verbose_name='Автоматически продлевать?',
        default=True,
        **NOT_NULLABLE
    )
    verified_payment_id = models.CharField(
        verbose_name='Подтвержденный ID платежа (автоплатежи)',
        max_length=128,
        **NULLABLE,
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='subscriptions',
        on_delete=models.CASCADE,
        **NOT_NULLABLE
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Продукт',
        related_name='subscriptions',
        on_delete=models.DO_NOTHING,
        **NOT_NULLABLE
    )
    payment_amount = models.FloatField(
        verbose_name='Цена подписки',
        **NOT_NULLABLE,
    )
    payment_currency = models.CharField(
        verbose_name='Валюта платежа',
        max_length=128,
        choices=PaymentCurrency.choices,
        default=PaymentCurrency.RUB,
        **NOT_NULLABLE,
    )
    payment_system = models.CharField(
        verbose_name='Платежная система',
        max_length=128,
        default='YooKassa',
        **NOT_NULLABLE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f"Подписка {self.user} -> {self.product}"
