from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.shop.api.serializers.user import (
    BalanceTopUpSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
)
from apps.shop.api.services import user_deposit_balance
from apps.shop.models import User


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Пользователи"],
        summary="Регистрация нового пользователя",
        responses={status.HTTP_201_CREATED: UserProfileSerializer},
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().post(request, *args, **kwargs)


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Пользователи"], summary="Получить профиль текущего пользователя"
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    def get_object(self) -> User:
        return self.request.user


class BalanceTopUpView(generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = BalanceTopUpSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Пользователи"],
        summary="Пополнить личный баланс",
        description="Увеличивает баланс пользователя на указанную сумму",
        request=BalanceTopUpSerializer,
        responses={status.HTTP_200_OK: UserProfileSerializer},
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = user_deposit_balance(
            user_id=request.user.id,
            amount=serializer.validated_data["amount"],
        )
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)


# через generics.GenericAPIView

# class BalanceTopUpView(generics.GenericAPIView):
#     serializer_class = BalanceTopUpSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = user_deposit_balance(
#             user_id=request.user.id,
#             amount=serializer.validated_data["amount"],
#         )
#         return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

# или всё в одном месте

# class UserViewSet(viewsets.GenericViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserProfileSerializer


#     def get_serializer_class(self) -> type[BaseSerializer[Any]]:
#         match self.action:
#             case "create":
#                 return UserRegisterSerializer
#             case "top_up":
#                 return BalanceTopUpSerializer
#             case _:
#                 return UserProfileSerializer

#     def get_permissions(self) -> list[permissions.BasePermission]:
#         if self.action == "create":
#             return [permissions.AllowAny()]
#         return [permissions.IsAuthenticated()]

#     def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user: User = serializer.save()

#         response_serializer = UserProfileSerializer(
#             instance=user,
#             context=self.get_serializer_context(),
#         )
#         return Response(response_serializer.data, status=status.HTTP_201_CREATED)

#     @action(
#         methods=["get"],
#         detail=False,
#         url_path="me",
#     )
#     def me(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         serializer = self.get_serializer(instance=request.user)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     @action(
#         methods=["post"],
#         detail=False,
#         url_path="top-up",
#     )
#     def top_up(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = user_deposit_balance(
#             user_id=request.user.id,
#             amount=serializer.validated_data["amount"],
#         )
#         response_serializer = UserProfileSerializer(
#             instance=user,
#             context=self.get_serializer_context(),
#         )
#         return Response(response_serializer.data, status=status.HTTP_200_OK)
