from django.conf import settings
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from integrations.telegram.auth import build_deep_link

from . import services
from .models import TelegramAuthChallenge
from .serializers import LoginCodeVerifySerializer
from .services import CHALLENGE_TTL_SECONDS
from .throttles import TelegramChallengeThrottle, TelegramVerifyThrottle


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfCookieView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "ok"})


class TelegramTokenCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [TelegramChallengeThrottle]

    def post(self, request):
        raw_token, challenge = services.create_auth_challenge(ip=_client_ip(request))
        deep_link = build_deep_link(settings.TELEGRAM_BOT_USERNAME, raw_token)
        return Response(
            {
                "token": raw_token,
                "deep_link": deep_link,
                "expires_at": challenge.expires_at.isoformat(),
                "expires_in_seconds": CHALLENGE_TTL_SECONDS,
            },
            status=201,
        )


class TelegramTokenStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        challenge = services.get_auth_challenge_status(token)

        if challenge is None or challenge.is_expired():
            return Response({"status": "expired"})

        if challenge.status != TelegramAuthChallenge.STATUS_CONFIRMED:
            return Response({"status": "pending"})

        # Idempotent login-on-poll: only actually log in the browser once.
        if challenge.session_issued_at is None and challenge.user_id is not None:
            login(request, challenge.user)
            services.mark_challenge_session_issued(challenge)

        return Response({"status": "confirmed"})


class TelegramCodeVerifyView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [TelegramVerifyThrottle]

    def post(self, request):
        serializer = LoginCodeVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "invalid", "detail": "5 xonali kod kiriting."}, status=400
            )

        raw_code = serializer.validated_data["code"]
        user, error = services.verify_login_code(raw_code)

        if error is not None:
            messages = {
                "invalid": "Kod topilmadi yoki noto'g'ri.",
                "used": "Bu kod allaqachon ishlatilgan.",
                "expired": "Kodning amal qilish muddati tugagan.",
            }
            return Response({"status": error, "detail": messages[error]}, status=400)

        login(request, user)
        return Response({"status": "ok"})


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({"status": "ok"})
