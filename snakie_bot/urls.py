from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('users/', include('user.urls'), name='users'),
    path('payments/', include('payment.urls'), name='payments'),
    path('', admin.site.urls),
]
