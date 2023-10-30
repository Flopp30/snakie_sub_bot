from django.contrib import admin
from django.utils.html import format_html

from user.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'chat_id', 'username', 'link_', 'send_message_', 'last_visit_time', 'registration_datetime',
        'first_sub_date', 'state'
    )
    list_filter = (
        'last_visit_time',
        'registration_datetime',
        'first_sub_date', 'state'
    )
    ordering = ('-id', 'username', 'last_visit_time')
    list_per_page = 20
    list_prefetch_related = ['subscriptions', ]
    search_fields = ('username', 'state')

    def link_(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.link,
            obj,
        )

    link_.short_description = 'TG link'

    def send_message_(self, obj):
        return format_html(
            f'<button userId={obj.pk} type="button" class="custom-button send-msg-btn">Сообщение</button>'
        )

    send_message_.short_description = 'Отправить сообщение'
