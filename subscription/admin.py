from datetime import datetime

from django.contrib import admin
from django.utils.html import format_html
from rangefilter.filters import DateRangeQuickSelectListFilterBuilder

from subscription.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'is_active', 'is_auto_renew', 'first_sub_', 'first_coming_', 'start_date', 'unsub_date', 'user_',
        'product',
        'payment_amount', 'payment_currency'
    )
    list_filter = (
        (
            "user__registration_datetime",
            DateRangeQuickSelectListFilterBuilder(
                title="Дата регистрации пользователя",
                default_start=datetime.now(),
                default_end=datetime.now(),
            ),
        ),
        (
            "user__first_sub_date",
            DateRangeQuickSelectListFilterBuilder(
                title="Дата первой подписки",
                default_start=datetime.now(),
                default_end=datetime.now(),
            ),
        ),
        (
            "start_date",
            DateRangeQuickSelectListFilterBuilder(
                title="Дата начала подписки",
                default_start=datetime.now(),
                default_end=datetime.now(),
            ),
        ),
        (
            "unsub_date",
            DateRangeQuickSelectListFilterBuilder(
                title="Дата окончания подписки подписки",
                default_start=datetime.now(),
                default_end=datetime.now(),
            ),
        ),
        'is_auto_renew',
        'is_active',
        'product',
    )
    ordering = ('-id', '-unsub_date', '-start_date')
    list_per_page = 20
    list_select_related = ['user', 'product']
    search_fields = ('payment_amount', 'id', 'user__username', "user__chat_id")

    def user_(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.user.link,
            obj.user,
        )

    user_.short_description = 'TG link'

    def first_sub_(self, obj):
        return obj.user.first_sub_date

    first_sub_.short_description = 'Дата первой подписки'
    first_sub_.admin_order_field = 'user__first_sub_date'

    def first_coming_(self, obj):
        return obj.user.registration_datetime

    first_coming_.short_description = 'Дата регистрации пользователя'
    first_coming_.admin_order_field = 'user__registration_datetime'
