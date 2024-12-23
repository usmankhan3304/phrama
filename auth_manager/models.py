from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
import random

User = get_user_model()

class TemporaryUserData(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()
    password = models.CharField(max_length=128)  # Ensure this is encrypted or handled securely

    def __str__(self):
        return self.username

class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null= True)
    temp_user = models.OneToOneField(TemporaryUserData, on_delete=models.CASCADE,blank=True, null= True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_otp():
        return ''.join([str(random.randint(0, 9)) for _ in range(4)])


class PasswordResetState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return self.expires_at < timezone.now()

