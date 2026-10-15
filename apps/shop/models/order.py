from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.shop.models.product import Product


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "В обработке"
    COMPLETED = "COMPLETED", "Выполнен"
    CANCELLED = "CANCELLED", "Отменён"


class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Пользователь",  # ?
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="in_carts",
        verbose_name="Товар",
    )

    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name="Количество"
    )

    class Meta:
        verbose_name = "Позиция в корзине"
        verbose_name_plural = "Позиции в корзине"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_cart_product",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="cart_item_quantity_gt_zero",
            ),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.product.name} (кол-во -  {self.quantity})"


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Покупатель",
    )

    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Итоговая стоимость"
    )

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.COMPLETED,
        verbose_name="Статус",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

        ordering = ["-created_at"]

        (
            models.CheckConstraint(
                condition=models.Q(status__in=OrderStatus.values),
                name="orders_order_status_valid",
            ),
        )
        (
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=Decimal("0.00")),
                name="orders_order_total_amount_non_negative",
            ),
        )

    def __str__(self):
        return f"Заказ №{self.id}: {self.user.username} ({self.total_amount} руб.)"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="ordered_in",  # ?
        verbose_name="Товар",
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Количество"
    )  # ?

    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена при покупке",
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="unique_order_product",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="order_item_quantity_gt_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(price_at_purchase__gte=Decimal("0.00")),
                name="order_item_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity}"
