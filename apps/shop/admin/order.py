from django.contrib import admin

from apps.shop.models import CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "quantity", "price_at_purchase"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "total_amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    inlines = [OrderItemInline]
    readonly_fields = ["total_amount", "created_at"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "quantity"]
