from urllib.parse import urlencode
from django.contrib.auth import login
from django.shortcuts import redirect
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .service import (
    GoogleRawLoginFlowService,
)
from users.selectors import user_list
from users.services import user_get_or_create

class PublicApi(APIView):
    authentication_classes = ()
    permission_classes = ()


class GoogleLoginRedirectApi(PublicApi):
    def get(self, request, *args, **kwargs):
        google_login_flow = GoogleRawLoginFlowService()

        authorization_url, state = google_login_flow.get_authorization_url()

        request.session["google_oauth2_state"] = state

        return redirect(authorization_url)


class GoogleLoginApi(PublicApi):
    class InputSerializer(serializers.Serializer):
        code = serializers.CharField(required=False)
        error = serializers.CharField(required=False)
        state = serializers.CharField(required=False)

    def get(self, request, *args, **kwargs):
        input_serializer = self.InputSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        code = validated_data.get("code")
        error = validated_data.get("error")
        state = validated_data.get("state")

        if error is not None:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        if code is None or state is None:
            return Response({"error": "Code and state are required."}, status=status.HTTP_400_BAD_REQUEST)

        # session_state = request.session.get("google_oauth2_state")

        # if session_state is None:
        #     return Response({"error": "CSRF check failed."}, status=status.HTTP_400_BAD_REQUEST)

        # del request.session["google_oauth2_state"]

        # if state != session_state:
        #     return Response({"error": "CSRF check failed."}, status=status.HTTP_400_BAD_REQUEST)

        google_login_flow = GoogleRawLoginFlowService()

        google_tokens = google_login_flow.get_tokens(code=code)

        id_token_decoded = google_tokens.decode_id_token()
        user_info = google_login_flow.get_user_info(google_tokens=google_tokens)
        
        
        profile_data = {
            'email': user_info['email'],
            'first_name': user_info.get('given_name', ''),
            'last_name': user_info.get('family_name', ''),
        }

        # We use get-or-create logic here for the sake of the example.
        # We don't have a sign-up flow.
        user, _ = user_get_or_create(**profile_data)
        # This will get or create a token for the user
        token, _ = Token.objects.get_or_create(user=user)

        # user_email = id_token_decoded["email"]
        # request_user_list = user_list(filters={"email": user_email})
        # user = request_user_list.get() if request_user_list else None

        # if user is None:
        #     return Response({"error": f"User with email {user_email} is not found."}, status=status.HTTP_404_NOT_FOUND)

        login(request, user)

        result = {
            "token": token.key,
            "id_token_decoded": id_token_decoded,
            "user_info": user_info,
        }

        # Prepare the redirection URL
        frontend_url = "http://localhost:3000/login"  # Your frontend URL
        query_params = urlencode({'token': token.key})  # Encode token key as query parameter
        redirect_url = f"{frontend_url}?{query_params}"  # Append token to the frontend URL

        return redirect(redirect_url)
        #return Response(result, status=status.HTTP_200_OK)