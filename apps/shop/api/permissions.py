from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
