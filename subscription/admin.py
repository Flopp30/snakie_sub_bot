from django.contrib import admin
from django.utils.html import format_html

from subscription.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'is_active', 'is_auto_renew', 'start_date', 'unsub_date', 'user_', 'product',
        'payment_amount', 'payment_currency'
    )
    list_filter = (
        'start_date',
        'unsub_date',
        'is_auto_renew'
    )
    ordering = ('-id', '-unsub_date', '-start_date')
    list_per_page = 20
    list_select_related = ['user', 'product']
    search_fields = ('payment_amount', 'id')

    def user_(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.user.link,
            obj.user,
        )

    user_.short_description = 'TG link'
