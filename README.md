# CRM + subscription. Telegram bot

Check <a href="https://web.telegram.org/k/#@SnackieBirdSubscribeBot">here</a>

### Stack
- <a href="https://www.python.org/">Python 3.11 +</a>
- <a href="https://www.djangoproject.com/">Django 4.2.*</a>
- <a href="https://python-telegram-bot.org/">Python-telegram-bot 20.4</a>

### Modules
- snakie_bot : main app with settings.
- bot_parts : all about bot and business logic.
- message_templates : models for bot messages
- payment : all about payments and refund (models, views for payment systems callbacks, etc..)
- product : business models for products
- subscription : business models for subscription
- user : models for user, views for send message from admins
- utils : 
    - services - yookassa payments help module
    - helpers - utility functions for all modules

### Hints
- In memory objects:
    * bot_parts.models.OwnedBot - db model.
    * bot_parts.models.OwnedBotsInMemory - an object for storing rarely updated objects in RAM.<br>
      Reload on init, on models update (a command in the bot or django signal) and a periodic task.
- In the future:
  * YooPaymentCallBackView - need to refactor and update to async. <br>
    All the logic for creating, updating and deleting subscriptions is here
  * admin.py in all modules. Add filters and groupings.


