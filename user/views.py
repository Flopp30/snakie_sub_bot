from django.shortcuts import redirect
from django.views import View
from snakie_bot.tasks import send_to_user_task

class SendMessageView(View):
    return_url = '/user/user/'

    def post(self, request, **kwargs):
        to_users = request.POST.get('to_users')
        user_pk = request.POST.get('user_id')
        text = request.POST.get('message_text')
        with_keyboard = to_users == "all_unsub" and request.POST.get("with_keyboard") == "true"
        image_file = request.FILES.get('image')
        if image_file:
            image_file = image_file.read()
        send_to_user_task.apply_async(args=[to_users, user_pk, text, with_keyboard, image_file])
        return redirect(self.return_url)
