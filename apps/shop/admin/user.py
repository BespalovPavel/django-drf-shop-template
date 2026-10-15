from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.shop.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("Финансы", {"fields": ("balance",)}),)
    list_display = ["username", "email", "balance", "is_staff"]
