# Generated by Django 4.2.6 on 2023-10-08 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название шаблона')),
                ('content', models.TextField(blank=True, default='', verbose_name='Текст шаблона')),
            ],
            options={
                'verbose_name': 'Шаблон',
                'verbose_name_plural': 'Шаблоны',
            },
        ),
    ]
