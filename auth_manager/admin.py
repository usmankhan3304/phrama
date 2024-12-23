from django.contrib import admin
from .models import OTPVerification, PasswordResetState,TemporaryUserData
# Register your models here.
admin.site.register(OTPVerification)
admin.site.register(PasswordResetState)
admin.site.register(TemporaryUserData)