
from urllib.parse import urlencode
from django.contrib.auth import login
from django.shortcuts import redirect
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .service import MicrosoftAuthFlowService
from users.services import user_get_or_create

class PublicApi(APIView):
    authentication_classes = ()
    permission_classes = ()

class MicrosoftLoginRedirectApi(PublicApi):
    def get(self, request, *args, **kwargs):
        ms_auth_service = MicrosoftAuthFlowService()
        authorization_url, state = ms_auth_service.get_authorization_url()
        request.session["microsoft_oauth2_state"] = state
        return redirect(authorization_url)


class MicrosoftLoginApi(PublicApi):
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

        ms_auth_service = MicrosoftAuthFlowService()
        token_response = ms_auth_service.get_tokens(code=code)
        user_info = ms_auth_service.get_user_info(token_response['access_token'])

        profile_data = {
            'email': user_info['mail'],  # Adjust based on the actual key in Microsoft's response
            'first_name': user_info.get('givenName', ''),
            'last_name': user_info.get('surname', ''),
        }

        user, _ = user_get_or_create(**profile_data)
        token, _ = Token.objects.get_or_create(user=user)

        login(request, user)

        result = {
            "token": token.key,
            "user_info": user_info,
        }
        
        # Prepare the redirection URL
        frontend_url = "http://localhost:3000"  # frontend URL
        query_params = urlencode({'token': token.key})  # Encode token key as query parameter
        redirect_url = f"{frontend_url}?{query_params}"  # Append token to the frontend URL

        return redirect(redirect_url)

        #return Response(result, status=status.HTTP_200_OK)