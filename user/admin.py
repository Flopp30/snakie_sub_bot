import logging
from datetime import datetime

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from subscription.models import Subscription
from user.admin_actions import block_in_all_bots, unban_in_all_bots, ban_in_beginner_bot, ban_in_rookie_bot, \
    ban_in_advanced_bot, ban_in_bands_bot, unban_in_beginner_bot, unban_in_rookie_bot, unban_in_advanced_bot, \
    unban_in_bands_bot
from user.models import User
from rangefilter.filters import (
    DateRangeQuickSelectListFilterBuilder,
)


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
    actions = [
        block_in_all_bots,
        unban_in_all_bots,
        ban_in_beginner_bot,
        ban_in_rookie_bot,
        ban_in_advanced_bot,
        ban_in_bands_bot,
        unban_in_beginner_bot,
        unban_in_rookie_bot,
        unban_in_advanced_bot,
        unban_in_bands_bot,
    ]
    list_display = (
        'id', 'is_active_', 'chat_id', 'username', 'link_', 'send_message_', 'last_visit_time', 'registration_datetime',
        'first_sub_date', 'state'
    )
    list_filter = (
        IsSubscriberFilter,
        (
            "first_sub_date",
            DateRangeQuickSelectListFilterBuilder(
                title="Дата первой подписки",
                default_start=datetime.now(),
                default_end=datetime.now(),
            ),
        ),
        (
            'last_visit_time',
            DateRangeQuickSelectListFilterBuilder(
                title="Дата последнего посещения",
                default_start=datetime.now(),
                default_end=datetime.now(),
            ),
        ),
        (
            'registration_datetime',
            DateRangeQuickSelectListFilterBuilder(
                title="Дата и время регистрации",
                default_start=datetime.now(),
                default_end=datetime.now(),
            ),
        ),
        'state',
        'is_superuser',
    )
    ordering = ('-id', 'username', 'last_visit_time')
    list_per_page = 20
    list_prefetch_related = ['subscriptions', ]
    search_fields = ('username', 'state', 'chat_id')

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
