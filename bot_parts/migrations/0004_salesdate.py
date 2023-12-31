# Generated by Django 4.2.6 on 2023-10-29 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_parts', '0003_afterpaymentcontent'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False, verbose_name='Активна?')),
                ('start_date', models.DateTimeField(verbose_name='Старт')),
                ('end_date', models.DateTimeField(verbose_name='Конец')),
            ],
            options={
                'verbose_name': 'Дата продаж',
                'verbose_name_plural': 'Даты продаж',
                'unique_together': {('start_date', 'end_date')},
            },
        ),
    ]
