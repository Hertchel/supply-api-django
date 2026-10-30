import logging
# from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
# from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from .utils import set_current_user

logger = logging.getLogger(__name__)

"""
def is_token_blacklisted(token):
    return BlacklistedToken.objects.filter(token__jti=token["jti"]).exists()
"""



import time

class CookieJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        total_start = time.perf_counter()

        auth_header = self.get_header(request)
        token = self.get_raw_token(auth_header) if auth_header else None

        if token is None:
            token = request.COOKIES.get("access_token")

        if not token:
            return None

        try:
            start = time.perf_counter()
            validated_token = self.get_validated_token(token)
            jwt_time = time.perf_counter() - start

            user_id = validated_token.get("user_id")

            if not user_id:
                raise AuthenticationFailed(
                    "Invalid token: user_id not found"
                )

            start = time.perf_counter()
            user = self.get_user(validated_token)
            user_time = time.perf_counter() - start

            start = time.perf_counter()
            set_current_user(user)
            context_time = time.perf_counter() - start

            total_time = time.perf_counter() - total_start

            logger.info(
                "[AUTH TIMING] JWT: %.4fs | USER DB: %.4fs | "
                "USER CONTEXT: %.4fs | TOTAL: %.4fs",
                jwt_time,
                user_time,
                context_time,
                total_time,
            )

            return (user, validated_token)

        except AuthenticationFailed:
            raise

        except Exception as e:
            logger.exception("Error during JWT authentication")
            raise AuthenticationFailed(
                f"Error retrieving user: {str(e)}"
            )

