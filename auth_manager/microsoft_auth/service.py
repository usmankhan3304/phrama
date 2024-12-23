import uuid
from django.conf import settings
import jwt
import requests
import msal

class MicrosoftAuthFlowService:
    def __init__(self):
        self.client_id = settings.MICROSOFT_OAUTH2_CLIENT_ID
        self.client_secret = settings.MICROSOFT_SECRET_VALUE
        self.redirect_uri = 'http://localhost:8000/api/auth/login/microsoft/callback/'
        self.authority = "https://login.microsoftonline.com/common"
        self.scopes = ["openid email profile User.Read"]

        self.client = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
            token_cache=None  # You can configure this to use a more persistent cache
        )

    def get_authorization_url(self):
        state = str(uuid.uuid4())
        auth_url = self.client.get_authorization_request_url(self.scopes, state=state, redirect_uri=self.redirect_uri)
        return auth_url, state

    def get_tokens(self, code):
        token_response = self.client.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes, 
            redirect_uri=self.redirect_uri
        )
        return token_response

    def decode_id_token(self, id_token):
        # Optional: Provide method to decode ID Token
        return jwt.decode(id_token, options={"verify_signature": False})

    def get_user_info(self, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        return user_info_response.json()
