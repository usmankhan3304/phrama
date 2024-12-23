from django.urls import path

from .views import (
    GoogleLoginApi,
    GoogleLoginRedirectApi,
)

urlpatterns = [
    path("callback/", GoogleLoginApi.as_view(), name="callback"),
    path("redirect/", GoogleLoginRedirectApi.as_view(), name="redirect"),
]


#http://127.0.0.1:8000/api/auth/login/google/redirect