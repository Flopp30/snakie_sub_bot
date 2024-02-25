from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from snakie_bot.tasks import send_to_user_task


class SendMessageView(View):
    return_url = '/user/user/'
    success_message = 'Задача на отправку сообщений поставлена успешно.'
    with_image_to_long_error = ('Слишком длинное сообщение (разрешенная длинна '
                                'с картинкой - 1024 символа, По факту - {real_len}')
    without_image_to_long_error = ('Слишком длинное сообщение (разрешенная длинна '
                                   '- 4096 символа, По факту - {real_len}')

    def post(self, request, **kwargs):
        to_users = request.POST.get('to_users')
        user_pk = request.POST.get('user_id')
        text = request.POST.get('message_text')
        if len(text) > 4096:
            messages.error(request, self.get_error_message(with_image=False, real_len=len(text)))
            return redirect(self.return_url)
        with_keyboard = to_users == "all_unsub" and request.POST.get("with_keyboard") == "true"
        image_file = request.FILES.get('image')
        if image_file:
            if len(text) > 1024:
                messages.error(request, self.get_error_message(with_image=True, real_len=len(text)))
                return redirect(self.return_url)
            image_file = image_file.read()
        send_to_user_task.apply_async(args=[to_users, user_pk, text, with_keyboard, image_file])
        messages.success(request, self.success_message)
        return redirect(self.return_url)

    def get_error_message(self, real_len: int, with_image: bool = False):
        if with_image:
            return self.with_image_to_long_error.format(real_len=real_len)
        return self.without_image_to_long_error.format(real_len=real_len)
