# Generated by Django 4.2.6 on 2023-10-08 15:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
        ('subscription', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('succeeded', 'Succeeded'), ('canceled', 'Canceled')], max_length=128, verbose_name='Статус платежа')),
                ('payment_service_id', models.UUIDField(verbose_name='Id платежа в платежной системе')),
                ('payment_service', models.CharField(default='YooKassa', max_length=128, verbose_name='Платежная система')),
                ('amount', models.FloatField(verbose_name='Сумма платежа')),
                ('currency', models.CharField(choices=[('RUB', 'Rub'), ('USD', 'Usd'), ('EUR', 'Eur')], default='RUB', max_length=128, verbose_name='Валюта платежа')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('is_refunded', models.BooleanField(default=False, verbose_name='Возвращен?')),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='payments', to='subscription.subscription', verbose_name='Подписка')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='payments', to='user.user', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Платеж',
                'verbose_name_plural': 'Платежи',
            },
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('created', 'Created'), ('succeeded', 'Succeeded')], default='created', max_length=128, verbose_name='Статус')),
                ('payment_service_id', models.UUIDField(verbose_name='Id возврата в платежной системе')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('payment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='refund', to='payment.payment', verbose_name='Возврат')),
            ],
            options={
                'verbose_name': 'Возврат',
                'verbose_name_plural': 'Возвраты',
            },
        ),
    ]
