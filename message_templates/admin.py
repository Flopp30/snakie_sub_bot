from django.contrib import admin

from message_templates.models import Template


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'content',
    )
    ordering = ('-id',)
    list_per_page = 30
    search_fields = ('name', 'content')
