import logging
import uuid
from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    UnsupportedMediaType,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("api.exceptions")


# ==============================================================================
# БАЗОВЫЕ И ДОМЕННЫЕ ИСКЛЮЧЕНИЯ МАГАЗИНА
# ==============================================================================


class ShopAPIException(APIException):
    """Базовое исключение для магазина."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Произошла ошибка сервера"
    default_code = "server_error"

    def __init__(self, detail=None, code=None, status_code=None):
        super().__init__(detail, code)
        if status_code:
            self.status_code = status_code


class InsufficientStockError(ShopAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Недостаточно товара на складе"
    default_code = "insufficient_stock"


class InsufficientBalanceError(ShopAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Недостаточно средств на балансе"
    default_code = "insufficient_balance"


class EmptyCartError(ShopAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Нельзя оформить заказ из пустой корзины"
    default_code = "empty_cart"


class ItemNotFoundError(ShopAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Запрашиваемый объект не найден"
    default_code = "not_found"


class InvalidQuantityError(ShopAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Количество товара должно быть строго больше нуля"
    default_code = "invalid_quantity"


class EmptyDepositError(ShopAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "INSUFFICIENT_DEPOSIT"
    message = "Недостаточная сумма для пополнения"


# ==============================================================================
# ОБРАБОТЧИК И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================


def get_client_ip(request) -> str | None:
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def format_validation_errors(validation_errors: Any) -> Any:
    if isinstance(validation_errors, dict):
        return {
            field: [str(err) for err in errors]
            if isinstance(errors, list)
            else [str(errors)]
            for field, errors in validation_errors.items()
        }
    if isinstance(validation_errors, list):
        return [str(error) for error in validation_errors]
    return [str(validation_errors)]


def log_exception(exc: Exception, context: dict, error_id: str) -> None:
    view = context.get("view")
    request = context.get("request")

    log_context = {
        "error_id": error_id,
        "exception_type": type(exc).__name__,
        "view": f"{view.__class__.__module__}.{view.__class__.__name__}"
        if view
        else None,
        "path": request.path if request else None,
        "method": request.method if request else None,
        "ip": get_client_ip(request),
    }

    if isinstance(exc, (ValidationError, PermissionDenied, NotFound, NotAuthenticated)):
        logger.warning(
            "API Warning [%s]: %s | context=%s", error_id, str(exc), log_context
        )
    elif isinstance(exc, ShopAPIException):
        logger.warning(
            "Business Logic Error [%s]: %s | context=%s",
            error_id,
            str(exc),
            log_context,
        )
    else:
        logger.error(
            "Internal Server Error [%s]: %s | context=%s",
            error_id,
            str(exc),
            log_context,
            exc_info=True,
        )


def build_error_response(
    exc: Exception, original_data: Any, request, error_id: str
) -> dict:
    error_response = {
        "error": True,
        "error_id": error_id,
        "timestamp": datetime.now().isoformat(),
        "path": request.path if request else None,
        "method": request.method if request else None,
    }

    # 1. Ошибки валидации полей сериализатора (400)
    if isinstance(exc, ValidationError):
        error_response.update(
            {
                "error_type": "validation_error",
                "message": "Ошибка валидации входных данных",
                "details": format_validation_errors(original_data),
                "code": getattr(exc, "default_code", "validation_error"),
            }
        )

    # 2. Бизнес-ошибки нашего магазина (баланс, остатки, корзина)
    elif isinstance(exc, ShopAPIException):
        error_response.update(
            {
                "error_type": "business_error",
                "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
                "code": getattr(exc, "default_code", "business_error"),
            }
        )

    # 3. Пользователь не передал токен авторизации (401)
    elif isinstance(exc, NotAuthenticated):
        error_response.update(
            {
                "error_type": "authentication_required",
                "message": "Требуется аутентификация",
                "code": "not_authenticated",
            }
        )

    # 4. Пользователь передал неверный логин/пароль или битый токен (401)
    elif isinstance(exc, AuthenticationFailed):
        error_response.update(
            {
                "error_type": "authentication_failed",
                "message": str(exc.detail)
                if hasattr(exc, "detail")
                else "Ошибка проверки подлинности",
                "code": getattr(exc, "default_code", "authentication_failed"),
            }
        )

    # 5. Пользователю не хватает прав (403 Forbidden)
    elif isinstance(exc, PermissionDenied):
        error_response.update(
            {
                "error_type": "permission_denied",
                "message": str(exc.detail)
                if hasattr(exc, "detail")
                else "Доступ запрещен",
                "code": "permission_denied",
            }
        )

    # 6. Объект или страница пагинации не найдена (404)
    elif isinstance(exc, NotFound):
        error_response.update(
            {
                "error_type": "not_found",
                "message": str(exc.detail)
                if hasattr(exc, "detail")
                else "Ресурс не найден",
                "code": "not_found",
            }
        )

    # 7. Отправлен не тот HTTP-метод (например, POST вместо GET) (405)
    elif isinstance(exc, MethodNotAllowed):
        error_response.update(
            {
                "error_type": "method_not_allowed",
                "message": f"Метод {request.method if request else ''} не разрешен для данного эндпоинта",
                "code": "method_not_allowed",
            }
        )

    # 8. Превышен лимит запросов Rate Limiting (429)
    elif isinstance(exc, Throttled):
        error_response.update(
            {
                "error_type": "rate_limit_exceeded",
                "message": "Превышен лимит запросов к API",
                "code": "throttled",
                "retry_after_seconds": exc.wait,
            }
        )

    # 9. Клиент прислал сломанный/невалидный JSON (400)
    elif isinstance(exc, ParseError):
        error_response.update(
            {
                "error_type": "parse_error",
                "message": "Ошибка синтаксиса JSON в теле запроса",
                "code": "parse_error",
            }
        )

    # 10. Отправлен неподдерживаемый заголовок Content-Type (415)
    elif isinstance(exc, UnsupportedMediaType):
        error_response.update(
            {
                "error_type": "unsupported_media_type",
                "message": "Неподдерживаемый тип содержимого (ожидается application/json)",
                "code": "unsupported_media_type",
            }
        )

    # Все прочие непредвиденные ошибки DRF
    else:
        detail_msg = (
            original_data.get("detail", "Произошла ошибка API")
            if isinstance(original_data, dict)
            else str(original_data)
        )
        error_response.update(
            {
                "error_type": "api_error",
                "message": detail_msg,
                "code": getattr(exc, "default_code", "api_error"),
            }
        )

    return error_response


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    response = drf_exception_handler(exc, context)
    request = context.get("request")
    error_id = str(uuid.uuid4())[:8]

    log_exception(exc, context, error_id)

    if response is not None:
        response.data = build_error_response(exc, response.data, request, error_id)
        if isinstance(exc, Throttled):
            response["Retry-After"] = exc.wait
    else:
        if isinstance(exc, DjangoValidationError):
            response = Response(
                {
                    "error": True,
                    "error_id": error_id,
                    "error_type": "validation_error",
                    "message": "Ошибка валидации данных",
                    "details": exc.message_dict
                    if hasattr(exc, "message_dict")
                    else [str(exc)],
                    "code": "validation_error",
                    "timestamp": datetime.now().isoformat(),
                    "path": request.path if request else None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif isinstance(exc, IntegrityError):
            err_msg = str(exc).lower()
            code = (
                "duplicate_entry"
                if ("unique" in err_msg or "duplicate" in err_msg)
                else "integrity_error"
            )
            status_code = (
                status.HTTP_409_CONFLICT
                if code == "duplicate_entry"
                else status.HTTP_400_BAD_REQUEST
            )
            response = Response(
                {
                    "error": True,
                    "error_id": error_id,
                    "error_type": "database_integrity_error",
                    "message": "Конфликт данных или нарушение связей в базе данных",
                    "code": code,
                    "timestamp": datetime.now().isoformat(),
                    "path": request.path if request else None,
                },
                status=status_code,
            )
        elif isinstance(exc, Http404):
            response = Response(
                {
                    "error": True,
                    "error_id": error_id,
                    "error_type": "not_found",
                    "message": "Запрашиваемый ресурс не найден",
                    "code": "not_found",
                    "timestamp": datetime.now().isoformat(),
                    "path": request.path if request else None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            response = Response(
                {
                    "error": True,
                    "error_id": error_id,
                    "error_type": "server_error",
                    "message": "Внутренняя ошибка сервера",
                    "code": "internal_server_error",
                    "timestamp": datetime.now().isoformat(),
                    "path": request.path if request else None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return response
