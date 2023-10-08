from django.db import models
from user.models import NOT_NULLABLE
from utils.models import PaymentCurrency


class SubPeriodTypes(models.TextChoices):
    month = 'by month'
    day = 'by day'


class Product(models.Model):
    displayed_name = models.CharField(
        verbose_name='Отображаемое имя',
        max_length=128,
        **NOT_NULLABLE
    )
    payment_name = models.CharField(
        verbose_name='Отображаемый срок подписки',
        max_length=128,
        **NOT_NULLABLE
    )
    amount = models.FloatField(
        verbose_name='Цена',
        default=0,
        **NOT_NULLABLE
    )
    currency = models.CharField(
        verbose_name='Валюта',
        max_length=128,
        choices=PaymentCurrency.choices,
        default=PaymentCurrency.RUB,
        **NOT_NULLABLE
    )
    sub_period = models.IntegerField(
        verbose_name='Срок подписки',
        default=1,
        **NOT_NULLABLE,
    )
    sub_period_type = models.CharField(
        verbose_name='Тип периода срока подписки',
        max_length=128,
        choices=SubPeriodTypes.choices,
        default=SubPeriodTypes.month
    )
    is_trial = models.BooleanField(
        verbose_name='Пробная?',
        default=False,
        **NOT_NULLABLE
    )
    is_active = models.BooleanField(
        verbose_name='Активен?',
        default=True,
        **NOT_NULLABLE,
    )

    def __str__(self):
        return f"{self.displayed_name} | {self.payment_name}"

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

