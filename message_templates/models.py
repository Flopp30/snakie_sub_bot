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


class MessageTemplatesInMemory:
    templates: dict[str, str] = {}
    default_message: str = 'Нет шаблона {key}'

    @classmethod
    def get(cls, key, default=None):
        # TODO remove both sync methods, when will you transfer payment views to async
        if not cls.templates:
            cls.load_templates()
        if not default:
            default = cls.default_message.format(key=key)
        return cls.templates.get(key, default)

    @classmethod
    def load_templates(cls, *args, **kwargs):
        cls.templates = {}
        for template in Template.objects.all():
            cls.templates[template.name] = (
                template.content
                .replace('<div>', '').replace('</div>', '')
                .replace('<br />', '').replace('&nbsp;', '')
                .replace('<p>', '').replace('</p>', '')
            )

    @classmethod
    async def aget(cls, key, default=None):
        if not cls.templates:
            await cls.aload_templates()
        if not default:
            default = cls.default_message.format(key=key)
        return cls.templates.get(key, default)

    @classmethod
    async def aload_templates(cls, *args, **kwargs):
        cls.templates = {}
        async for template in Template.objects.all():
            cls.templates[template.name] = (
                template.content
                .replace('<div>', '').replace('</div>', '')
                .replace('<br />', '').replace('&nbsp;', '')
                .replace('<p>', '').replace('</p>', '')
            )
