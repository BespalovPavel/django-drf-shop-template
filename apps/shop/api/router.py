from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.shop.api.views.order import (
    CartItemAddView,
    CartItemDetailView,
    CartView,
    OrderCheckoutView,
    OrderListView,
)
from apps.shop.api.views.product import ProductViewSet
from apps.shop.api.views.user import BalanceTopUpView, UserProfileView, UserRegisterView

router = DefaultRouter()

router.register(r"products", ProductViewSet, basename="product")

app_name = "shop"

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("balance/top-up/", BalanceTopUpView.as_view(), name="balance_top_up"),
    path("cart/", CartView.as_view(), name="cart-view"),
    path("cart/items/", CartItemAddView.as_view(), name="cart-add"),
    path(
        "cart/items/<int:product_id>/", CartItemDetailView.as_view(), name="cart-detail"
    ),
    # Заказы
    path("orders/checkout/", OrderCheckoutView.as_view(), name="order-checkout"),
    path("orders/", OrderListView.as_view(), name="order-list"),
]

urlpatterns += router.urls
