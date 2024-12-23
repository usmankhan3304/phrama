
from django.urls import include, path
from .views import *

login_urlpatterns = [
    #path("google-login/", include(("confg_django.auth.google_auth.urls", "google-login")),),
    path("google/", include(("auth_manager.google_auth.urls", "google")),),
    path("microsoft/", include(("auth_manager.microsoft_auth.urls", "microsoft")),)
]

urlpatterns = [
    path("login/", include(login_urlpatterns)),
    path("login/email/",UserLoginViewSet.as_view({"post": "login",}),name="login"),
    
    path('pre-signup/', UserPreSignupViewSet.as_view({'post': 'create'}), name='pre_signup'),
    path('signup/verify-otp/', VerifyAndCreateUser.as_view(), name='signup_verify_otp'),
    
    path('password/update/', PasswordUpdateAPI.as_view(), name='password_update'),
    path('password/reset/send-otp/', PasswordResetSendOTP.as_view(), name='password_reset_send_otp'),
    path('password/reset/verify-otp/', PasswordResetVerifyOTP.as_view(), name='password_reset_verify_otp'),
]