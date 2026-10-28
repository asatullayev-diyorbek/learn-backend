from rest_framework import serializers


class LoginCodeVerifySerializer(serializers.Serializer):
    code = serializers.RegexField(regex=r"^\d{5}$")


class CurrentUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    telegram_id = serializers.SerializerMethodField()
    telegram_username = serializers.SerializerMethodField()

    def get_telegram_id(self, user):
        identity = getattr(user, "telegram_identity", None)
        return identity.telegram_id if identity else None

    def get_telegram_username(self, user):
        identity = getattr(user, "telegram_identity", None)
        return identity.telegram_username if identity else ""
