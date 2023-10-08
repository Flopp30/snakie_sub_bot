from user.models import User


async def check_bot_context(update, context):
    if not context.user_data.get('user'):
        context.user_data['user'], _ = await User.objects.select_related('subscription').aget_or_create(
            chat_id=update.effective_chat.id,
            defaults={
                'username': update.effective_chat.username
            }
        )
