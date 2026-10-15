from decimal import Decimal

from rest_framework import serializers

from apps.shop.api.serializers.product import ProductSerializer
from apps.shop.models import CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "subtotal"]

    def get_subtotal(self, obj: CartItem) -> Decimal:
        return obj.product.price * obj.quantity


class CartAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)


class CartUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartListResponseSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)  # ?

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price_at_purchase"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "total_amount", "status", "created_at", "items"]

        read_only_fields = ["id", "total_amount", "status", "created_at"]
