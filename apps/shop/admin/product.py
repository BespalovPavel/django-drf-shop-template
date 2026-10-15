from django.contrib import admin

from apps.shop.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "price", "in_stock", "created_at"]
    search_fields = [
        "name",
    ]
    list_editable = ["price", "in_stock"]
