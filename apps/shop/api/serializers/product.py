from rest_framework import serializers

from apps.shop.models import Product


class ProductSerializer(serializers.ModelSerializer):
    in_stock = serializers.IntegerField(min_value=0)

    class Meta:
        model = Product

        fields = "__all__"

        read_only_fields = ["id", "created_at", "updated_at"]
