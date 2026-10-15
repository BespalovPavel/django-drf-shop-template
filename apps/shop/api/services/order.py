from decimal import Decimal

from django.db import transaction

from apps.shop.api.notifications import send_order_success_notification
from apps.shop.models import CartItem, Order, OrderItem, OrderStatus, Product, User
from custom_exceptions import (
    EmptyCartError,
    InsufficientBalanceError,
    InsufficientStockError,
    InvalidQuantityError,
    ItemNotFoundError,
)


def cart_add_item(*, user: User, product_id: int, quantity: int) -> CartItem:
    """Добавляет товар в корзину или увеличивает его количество"""

    if quantity <= 0:
        raise InvalidQuantityError("Количество должно быть строго больше нуля!")

    product = Product.objects.filter(id=product_id).first()

    if not product:
        raise ItemNotFoundError(f"Товар с ID {product_id} не найден в каталоге!")

    cart_item, created = CartItem.objects.get_or_create(
        user=user, product=product, quantity=quantity
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save(update_fields=["quantity"])

    return cart_item


def cart_update_item(*, user: User, product_id: int, quantity: int) -> CartItem:
    """Обновляет количество товара в корзине"""

    if quantity <= 0:
        raise InvalidQuantityError("Количество должно быть строго больше нуля!")

    try:
        cart_item = CartItem.objects.get(user=user, product_id=product_id)
        cart_item.quantity = quantity
        cart_item.save(update_fields=["quantity"])
        return cart_item
    except CartItem.DoesNotExist:
        raise ItemNotFoundError(f"Товар с ID {product_id} в корзине не найден!")


def cart_remove_item(*, user: User, product_id: int) -> None:
    """Удаляет позицию из корзины"""
    CartItem.objects.filter(user=user, product_id=product_id).delete()


def create_order_from_cart(*, user_id: User) -> Order:
    """Оформление заказа из корзины"""
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=user_id)

        cart_items = list(
            CartItem.objects.filter(user=user)
        )  # select_related("product"))

        if not cart_items:
            raise EmptyCartError("Нельзя оформить заказ из пустой корзины")

        locked_products = (
            Product.objects.select_for_update()
            .order_by("id")
            .in_bulk(item.product_id for item in cart_items)
        )

        total_amount = Decimal("0.00")
        for item in cart_items:
            product = locked_products.get(item.product_id)
            if not product:
                raise ItemNotFoundError(f"Товар ID {item.product_id} более недоступен")
            if product.stock < item.quantity:
                raise InsufficientStockError(
                    f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock}, требуется: {item.quantity}"
                )
            total_amount += product.price * item.quantity

        if user.balance < total_amount:
            raise InsufficientBalanceError(
                f"Недостаточно средств. Ваш баланс: {user.balance} руб., стоимость заказа: {total_amount} руб."
            )

        user.balance -= total_amount
        user.save(update_fields=["balance"])

        products_to_update: list[Product] = []
        for item in cart_items:
            product = locked_products[item.product_id]
            product.in_stock -= item.quantity
            products_to_update.append(product)

        Product.objects.bulk_update(products_to_update, fields=["in_stock"])

        order = Order.objects.create(
            user=user, total_amount=total_amount, status=OrderStatus.COMPLETED
        )

        order_items = [
            OrderItem(
                order=order,
                product=locked_products[item.product_id],
                quantity=item.quantity,
                price_at_purchase=locked_products[item.product_id].price,
            )
            for item in cart_items
        ]
        OrderItem.objects.bulk_create(order_items)

        CartItem.objects.filter(user=user).delete()

        transaction.on_commit(lambda: send_order_success_notification(order=order))

    return order
