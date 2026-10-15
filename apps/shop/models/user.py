from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models

# User = get_user_model()


class User(AbstractUser):
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Баланс",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

        ordering = ["-date_joined"]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=Decimal("0.00")),
                name="users_user_balance_non_negative",
            )
        ]

    def __str__(self) -> str:
        return f"{self.username} ({self.balance} руб.)"
