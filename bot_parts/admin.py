from django.contrib import admin

from bot_parts.models import OwnedBot, OwnedChat, AfterPaymentContent, SalesDate


@admin.register(OwnedBot)
class OwnedBotAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'chat_id'
    )
    ordering = ('-id', 'name')
    list_per_page = 20
    search_fields = ('name', 'chat_id')


@admin.register(OwnedChat)
class OwnedChatAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'chat_id'
    )
    ordering = ('-chat_id', 'name')
    list_per_page = 20
    search_fields = ('name', 'chat_id')


@admin.register(AfterPaymentContent)
class AfterPaymentContentAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'link'
    )
    ordering = ('-pk', 'name')
    list_per_page = 20
    search_fields = ('name', 'link')


@admin.register(SalesDate)
class SalesDateAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'is_active', 'start_date', 'end_date'
    )
    ordering = ('-pk', 'is_active')
    list_per_page = 20
    search_fields = ('start_date', 'end_date')
