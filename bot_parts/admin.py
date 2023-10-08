from django.contrib import admin

from bot_parts.models import OwnedBot, OwnedChat


@admin.register(OwnedBot)
class OwnedBotAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'chat_id'
    )
    ordering = ('-id', 'name')
    list_per_page = 20
    search_fields = ('name', 'chat_id')


@admin.register(OwnedChat)
class OwnedChat(admin.ModelAdmin):
    list_display = (
        'name', 'chat_id'
    )
    ordering = ('-chat_id', 'name')
    list_per_page = 20
    search_fields = ('name', 'chat_id')
