from rest_framework import serializers


class LoginCodeVerifySerializer(serializers.Serializer):
    code = serializers.RegexField(regex=r"^\d{5}$")
