from django.db.models.signals import post_save
from django.dispatch import receiver

from bot_parts.models import (
    AfterPaymentContent,
    ContentInMemory,
    OwnedChat,
    OwnedChatInMemory,
    OwnedBot,
    OwnedBotsInMemory,
)


@receiver(post_save, sender=AfterPaymentContent)
def reload_content_in_memory(sender, instance, **kwargs):
    ContentInMemory.load_contents()


@receiver(post_save, sender=OwnedChat)
def reload_content_in_memory(sender, instance, **kwargs):
    OwnedChatInMemory.reload_chats()


@receiver(post_save, sender=OwnedBot)
def reload_content_in_memory(sender, instance, **kwargs):
    OwnedBotsInMemory.reload_bots()

