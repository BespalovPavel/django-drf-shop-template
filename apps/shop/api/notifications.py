import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.shop.models import Order

logger = logging.getLogger("orders.notifications")


def send_order_success_notification(*, order: Order) -> None:
    """Логирует заказ в консоль и отправляет email-уведомление"""
    logger.info(
        "Заказ #%d успешно оформлен: покупатель=%s, сумма=%s руб.",
        order.id,
        order.user.username,
        order.total_amount,
    )

    if order.user.email:
        message = (
            f"Здравствуйте, {order.user.username}!\n\n"
            f"Ваш заказ #{order.id} на сумму {order.total_amount} руб. успешно оплачен.\n"
            f"Спасибо за покупку!"
        )

        send_mail(
            subject=f"Заказ #{order.id} успешно оформлен",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=True,
        )
