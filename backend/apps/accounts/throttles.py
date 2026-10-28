from rest_framework.throttling import ScopedRateThrottle


class TelegramChallengeThrottle(ScopedRateThrottle):
    scope = "telegram-challenge"


class TelegramVerifyThrottle(ScopedRateThrottle):
    scope = "telegram-verify"
