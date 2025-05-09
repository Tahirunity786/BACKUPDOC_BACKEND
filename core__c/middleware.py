from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_str):
    try:
        access_token = AccessToken(token_str)
        user_id = access_token.get("id")
        return User.objects.get(id=user_id)
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for Channels that authenticates users using JWT access tokens
    passed via query string in the WebSocket connection.
    """
    async def __call__(self, scope, receive, send):
        # Parse query string
        query_string = parse_qs(scope["query_string"].decode())
        token_list = query_string.get("token")

        if token_list:
            token = token_list[0]
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
