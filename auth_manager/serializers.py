from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinLengthValidator
from .models import OTPVerification


User = get_user_model()

class PreSignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}, 
        validators=[MinLengthValidator(8)]  
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

class VerifyEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)

    def validate(self, data):
        try:
            otp_record = OTPVerification.objects.get(temp_user__email=data['email'], otp=data['otp'])
            if otp_record.is_expired():
                raise serializers.ValidationError("OTP has expired.")
            return data
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP or email.")

    

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """ Check that the user with the provided email exists. """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user associated with this email address.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
   
    

class PasswordUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password fields didn't match."})
        return data