from decimal import Decimal

from django.db import transaction

from apps.shop.models import User
from custom_exceptions import EmptyDepositError


def user_deposit_balance(*, user_id: int, amount: Decimal) -> User:
    """Пополняет баланс пользователя"""
    if amount <= Decimal("0.00"):
        raise EmptyDepositError("Сумма пополнения должна быть строго больше нуля!")

    with transaction.atomic():
        user = User.objects.select_for_update().get(id=user_id)
        user.balance += amount

        user.save(update_fields=["balance"])
        return user
