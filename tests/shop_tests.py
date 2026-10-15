from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from custom_exceptions import (
    EmptyCartError,
    EmptyDepositError,
    InsufficientBalanceError,
    InsufficientStockError
)
from apps.shop.models import CartItem, Order, OrderItem, OrderStatus, Product, User
from apps.shop.api.services import (
    cart_add_item,
    cart_remove_item,
    cart_update_item,
    create_order_from_cart,
    user_deposit_balance
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def buyer() -> User:
    return User.objects.create_user(
        username="test_buyer",
        email="buyer@test.com",
        password="1234567890",
        balance=Decimal("200.00"),
    )


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_user(
        username="test_admin",
        email="admin@test.com",
        password="1234567890",
        is_staff=True,
    )


@pytest.fixture
def product() -> Product:
    return Product.objects.create(
        name="Банан",
        price=Decimal("70.00"),
        in_stock=5,
    )


@pytest.mark.django_db
def test_user_deposit_balance_success(buyer: User):
    updated_user = user_deposit_balance(user_id=buyer.id, amount=Decimal("350.00"))

    assert updated_user.balance == Decimal("550.00")
    buyer.refresh_from_db()
    assert buyer.balance == Decimal("550.00")


@pytest.mark.django_db
def test_user_deposit_negative_amount_raises_error(buyer: User):
    with pytest.raises(EmptyDepositError):
        user_deposit_balance(user_id=buyer.id, amount=Decimal("-1.00"))

    with pytest.raises(EmptyDepositError):
        user_deposit_balance(user_id=buyer.id, amount=Decimal("0.00"))


@pytest.mark.django_db
def test_cart_add_and_increment_quantity(buyer: User, product: Product):
    cart_add_item(user=buyer, product_id=product.id, quantity=2)
    cart_add_item(user=buyer, product_id=product.id, quantity=3)

    cart_item = CartItem.objects.get(user=buyer, product=product)
    assert cart_item.quantity == 5
    assert CartItem.objects.filter(user=buyer).count() == 1


@pytest.mark.django_db
def test_cart_update_and_remove_item(buyer: User, product: Product):
    cart_add_item(user=buyer, product_id=product.id, quantity=2)

    updated_item = cart_update_item(user=buyer, product_id=product.id, quantity=10)
    assert updated_item.quantity == 10

    cart_remove_item(user=buyer, product_id=product.id)
    assert CartItem.objects.filter(user=buyer).count() == 0


@pytest.mark.django_db
def test_order_fails_on_empty_cart(buyer: User):
    with pytest.raises(EmptyCartError):
        create_order_from_cart(user_id=buyer.id)


@pytest.mark.django_db
def test_public_can_view_products_but_cannot_create(
    api_client: APIClient, buyer: User, product: Product
):
    response_get = api_client.get("/api/products/")
    assert response_get.status_code == status.HTTP_200_OK

    api_client.force_authenticate(user=buyer)
    payload = {
        "name": "Новый товар",
        "price": "99.00",
        "in_stock": 10,
    }
    response_post = api_client.post("/api/products/", data=payload)
    assert response_post.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_create_product(api_client: APIClient, admin_user: User):
    api_client.force_authenticate(user=admin_user)
    payload = {
        "name": "Новый товар",
        "price": "99.00",
        "in_stock": 10,
    }
    response = api_client.post("/api/products/", data=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert Product.objects.filter(name="Новый товар").exists()


@pytest.mark.django_db
def test_successful_order_checkout(buyer: User, product: Product):
    cart_add_item(user=buyer, product_id=product.id, quantity=2)

    order = create_order_from_cart(user_id=buyer.id)

    assert order.status == OrderStatus.COMPLETED
    assert order.total_amount == Decimal("140.00")

    buyer.refresh_from_db()
    product.refresh_from_db()

    assert buyer.balance == Decimal("60.00")
    assert product.in_stock == 3
    assert buyer.cart_items.count() == 0


@pytest.mark.django_db
def test_order_fails_on_insufficient_balance(buyer: User, product: Product):
    buyer.balance = Decimal("50.00")
    buyer.save(update_fields=["balance"])

    cart_add_item(user=buyer, product_id=product.id, quantity=1)

    with pytest.raises(InsufficientBalanceError):
        create_order_from_cart(user_id=buyer.id)

    buyer.refresh_from_db()
    product.refresh_from_db()
    assert buyer.balance == Decimal("50.00")
    assert product.in_stock == 5


@pytest.mark.django_db
def test_order_fails_on_insufficient_in_stock(buyer: User, product: Product):
    buyer.balance = Decimal("5000.00")
    buyer.save(update_fields=["balance"])

    cart_add_item(user=buyer, product_id=product.id, quantity=10)

    with pytest.raises(InsufficientStockError):
        create_order_from_cart(user_id=buyer.id)

    product.refresh_from_db()
    assert product.in_stock == 5


@pytest.mark.django_db
def test_unauthorized_user_cannot_view_orders(api_client: APIClient):
    response = api_client.get("/api/orders/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_user_can_view_only_their_own_orders(
    api_client: APIClient, buyer: User, product: Product
):
    other_buyer = User.objects.create_user(
        username="other_buyer",
        email="other@test.com",
        password="1234567890",
        balance=Decimal("500.00"),
    )

    order_buyer = Order.objects.create(
        user=buyer,
        total_amount=Decimal("140.00"),
        status=OrderStatus.COMPLETED,
    )
    OrderItem.objects.create(
        order=order_buyer,
        product=product,
        quantity=2,
        price_at_purchase=Decimal("70.00"),
    )

    order_other = Order.objects.create(
        user=other_buyer,
        total_amount=Decimal("999.00"),
        status=OrderStatus.COMPLETED,
    )
    OrderItem.objects.create(
        order=order_other,
        product=product,
        quantity=1,
        price_at_purchase=Decimal("999.00"),
    )

    api_client.force_authenticate(user=buyer)
    response = api_client.get("/api/orders/")

    assert response.status_code == status.HTTP_200_OK

    data = response.data
    results = data["results"] if "results" in data else data

    assert len(results) == 1
    returned_order = results[0]

    assert returned_order["id"] == order_buyer.id
    assert Decimal(returned_order["total_amount"]) == Decimal("140.00")
    assert returned_order["status"] == OrderStatus.COMPLETED

    items = returned_order["items"]
    assert len(items) == 1
    assert items[0]["product"] == product.id
    assert items[0]["product_name"] == "Банан"
    assert items[0]["quantity"] == 2
    assert Decimal(items[0]["price_at_purchase"]) == Decimal("70.00")

    returned_ids = [o["id"] for o in results]
    assert order_other.id not in returned_ids
