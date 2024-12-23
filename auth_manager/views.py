# Create your views here.
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import *
from django.contrib.auth.models import User
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets

User = get_user_model()


class UserPreSignupViewSet(viewsets.ViewSet):
    def get_serializer_class(self):
        return PreSignupSerializer

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, **kwargs)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]

            temp_user_data, created = TemporaryUserData.objects.update_or_create(
                email=email, defaults={"username": username, "password": password}
            )

            OTPVerification.objects.filter(temp_user=temp_user_data).delete()
            otp = OTPVerification.generate_otp()
            OTPVerification.objects.create(
                temp_user=temp_user_data,  # Link OTP with temporary user data
                otp=otp,
                expires_at=timezone.now() + datetime.timedelta(minutes=30),
            )
            html_content = render_to_string(
                "emails/verification_email_otp.html", {"otp": otp}
            )
            text_content = strip_tags(html_content)
            send_mail(
                "Verify Your Email",
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [serializer.validated_data["email"]],
                html_message=html_content,
                fail_silently=False,
            )
            return Response(
                {
                    "success": True,
                    "message": "OTP sent to your email for verification.",
                },
                status=status.HTTP_200_OK,
            )
        else:
           
            return Response(
                {
                    "success": False,
                    #"message": "Invalid data",
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyAndCreateUser(APIView):
    def get_serializer_class(self):
        return VerifyEmailOTPSerializer

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                otp_record = OTPVerification.objects.get(
                    temp_user__email=serializer.validated_data["email"],
                    otp=serializer.validated_data["otp"],
                )
                temp_user_data = otp_record.temp_user

                # Create user from temporary data
                user = User.objects.create_user(
                    username=temp_user_data.username,
                    email=temp_user_data.email,
                    password=temp_user_data.password,
                )

                # Delete the temporary data and OTP record
                otp_record.delete()
                temp_user_data.delete()

                # Generate a token for the new user
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                return Response(
                    {
                        "success": True,
                        "message": "Account created successfully.",
                        "token": access_token,
                        #"refresh": refresh_token,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except OTPVerification.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Invalid OTP or email.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {
                    "success": False,
                    #"message": "Verification failed.",
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserLoginViewSet(viewsets.ModelViewSet):
    serializer_class = UserLoginSerializer

    @action(detail=False, methods=["POST"], url_path="login")
    def login(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                refresh = RefreshToken.for_user(user)
                user_info = {
                    "email": user.email,
                    "user_name": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "userId": str(user.id),
                }
                return Response(
                    {
                        "success": True,
                        "message": "Login successful.",
                        "data": {
                            #"refresh": str(refresh),
                            "token": str(refresh.access_token),
                            "user": user_info,
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"success": False, "message": "Incorrect password."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Password reset with OTP code
class PasswordResetSendOTP(APIView):
    #permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return SendOTPSerializer

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            user = User.objects.filter(email=email).first()
            if not user:
                return Response(
                    {
                        "success": False,
                        "message": "User with this email does not exist.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            otp = OTPVerification.generate_otp()

            # Check for existing PasswordResetState and update it
            state = PasswordResetState.objects.filter(user=user).first()
            if state:
                state.otp = otp
                state.otp_verified = False
                state.expires_at = timezone.now() + datetime.timedelta(minutes=30)
                state.save()
            else:
                # Create new PasswordResetState if none exists
                state = PasswordResetState.objects.create(
                    user=user, otp=otp, otp_verified=False, 
                    expires_at=timezone.now() + datetime.timedelta(minutes=30)
                )

            # Send email with OTP
            html_content = render_to_string(
                "emails/verification_email_otp.html", {"otp": otp}
            )
            text_content = strip_tags(html_content)
            send_mail(
                "Email Verification OTP",
                text_content,
                "",  # Replace with your actual email
                [email],
                html_message=html_content,
                fail_silently=False,
            )

            return Response(
                {
                    "success": True,
                    "message": "OTP sent to your email. Please verify to continue.",
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "success": False,
                    "message": "Failed to send OTP.",
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetVerifyOTP(APIView):
    #permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return VerifyOTPSerializer

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, **kwargs)

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data["otp"]
            email = serializer.validated_data["email"]  
            try:
                user = User.objects.get(email=email)  # Get user by email
                state = PasswordResetState.objects.get(user=user, otp=otp)
                if state.is_expired():
                    return Response(
                        {"success": False, "message": "OTP has expired."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                state.otp_verified = True
                state.save()

                return Response(
                    {
                        "success": True,
                        "message": "OTP verified. You can now update your password.",
                    },
                    status=status.HTTP_200_OK,
                )
            except User.DoesNotExist:
                return Response(
                    {"success": False, "message": "Invalid email."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except PasswordResetState.DoesNotExist:
                return Response(
                    {"success": False, "message": "Invalid OTP."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {
                "success": False,
                "message": "Invalid request.",
                "data": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class PasswordUpdateAPI(APIView):
    def get_serializer_class(self):
        return PasswordUpdateSerializer

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        
        # Check if the serializer is valid before accessing validated_data
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)  # Ensure user exists with the given email
            
            # Ensure OTP was verified before allowing password change
            if not PasswordResetState.objects.filter(user=user, otp_verified=True).exists():
                return Response(
                    {"success": False, "message": "OTP verification required."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            
            new_password = serializer.validated_data["new_password"]
            
            # Update the user's password
            user.set_password(new_password)
            user.save()

            # Generate new JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Clear the verification state
            PasswordResetState.objects.filter(user=user).delete()

            return Response({
                "success": True,
                "message": "Password updated successfully. Please use the new token for future requests.",
                "token": access_token,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "message": "Password update failed.",
                "data": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

