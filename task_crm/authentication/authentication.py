
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

class BlacklistJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        # 1. Perform standard JWT signature and expiration check
        validated_token = super().get_validated_token(raw_token)

        # 2. Extract JWT ID (jti)
        jti = validated_token.get("jti")

        # 3. Check if this specific Access Token's jti was blacklisted
        if jti and BlacklistedToken.objects.filter(token__jti=jti).exists():
            raise AuthenticationFailed("This token has been blacklisted / logged out.")

        return validated_token