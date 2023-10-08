from django.db import models


class PaymentCurrency(models.TextChoices):
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'
