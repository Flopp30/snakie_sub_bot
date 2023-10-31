from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from subscription.models import Subscription
from user.models import User


class IsSubscriberFilter(admin.SimpleListFilter):
    title = 'Подписан на клуб'
    parameter_name = 'is_active_'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        user_ids = (
            Subscription.objects
            .select_related('user')
            .filter(is_active=True)
            .values('user_id')
            .distinct()
        )
        if self.value() == 'yes':
            return queryset.filter(id__in=user_ids)
        if self.value() == 'no':
            return queryset.exclude(id__in=user_ids)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'is_active_', 'chat_id', 'username', 'link_', 'send_message_', 'last_visit_time', 'registration_datetime',
        'first_sub_date', 'state'
    )
    list_filter = (
        IsSubscriberFilter,
        'is_superuser',
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

    def is_active_(self, obj):
        res = '<img src="/static/admin/img/icon-yes.svg" alt="True">' if obj.subscriptions.filter(
            is_active=True).exists() else '<img src="/static/admin/img/icon-no.svg" alt="False">'
        return format_html(res)

    is_active_.short_description = 'Подписан?'
