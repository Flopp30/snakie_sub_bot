from django.db import models


class Template(models.Model):
    name = models.CharField(
        verbose_name='Название шаблона',
        max_length=100,
        null=False,
    )

    content = models.TextField(
        verbose_name="Текст шаблона",
        default='',
        blank=True,
    )

    class Meta:
        verbose_name = 'Шаблон'
        verbose_name_plural = 'Шаблоны'


class MessageTemplates:
    templates: dict[str, str] = {}
    default_message: str = 'Нет шаблона {key}'

    @classmethod
    def get(cls, key):
        return cls.templates.get(key, cls.default_message.format(key=key))

    @classmethod
    async def load_templates(cls, *args, **kwargs):
        cls.templates = {}
        async for template in Template.objects.all():
            cls.templates[template.name] = (
                template.content
                .replace('<div>', '').replace('</div>', '')
                .replace('<br />', '').replace('&nbsp;', '')
                .replace('<p>', '').replace('</p>', '')
            )