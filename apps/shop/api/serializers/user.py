from decimal import Decimal

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.shop.models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Пользователь с таким email уже зарегистрирован!",
            )
        ],
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User

        fields = ["id", "username", "email", "password", "balance", "date_joined"]
        read_only_fields = ["date_joined"]


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для User
    """

    class Meta:
        model = User

        fields = ["id", "username", "email", "balance"]
        read_only_fields = fields


class BalanceTopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
