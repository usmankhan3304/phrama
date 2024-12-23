from django.urls import path
from .views import *

urlpatterns = [
    path('redirect/', MicrosoftLoginRedirectApi.as_view(), name='redirect'),
    path('callback/', MicrosoftLoginApi.as_view(), name='callback'),
]


#http://127.0.0.1:8000/api/auth/login/microsoft/redirect