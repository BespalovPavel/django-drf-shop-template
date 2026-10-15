from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.shop.api.permissions import IsAdminOrReadOnly
from apps.shop.api.serializers.product import ProductSerializer
from apps.shop.models import Product


@extend_schema_view(
    list=extend_schema(tags=["Товары"], summary="Список товаров"),
    retrieve=extend_schema(tags=["Товары"], summary="Детальная информация о товаре"),
    create=extend_schema(tags=["Товары"], summary="Создать товар (только админ)"),
    update=extend_schema(
        tags=["Товары"], summary="Обновить товар целиком (только админ)"
    ),
    partial_update=extend_schema(
        tags=["Товары"], summary="Частично обновить товар (только админ)"
    ),
    destroy=extend_schema(tags=["Товары"], summary="Удалить товар (только админ)"),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    search_fields = ["name"]
