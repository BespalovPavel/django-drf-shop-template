from decimal import Decimal

from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=300, verbose_name="Название")

    description = models.TextField(blank=True, default="", verbose_name="Описание")

    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    in_stock = models.IntegerField(default=0, verbose_name="На складе")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменён")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=Decimal("0.00")),
                name="products_product_price_non_negative",
            )
        ]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return f"{self.name} | цена: {self.price} | на складе: {self.in_stock}"
