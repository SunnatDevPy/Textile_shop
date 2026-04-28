import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from config import conf

logger = logging.getLogger(__name__)


def _can_send_email() -> bool:
    return bool(
        conf.SMTP_ENABLED
        and conf.SMTP_HOST
        and conf.SMTP_PORT
        and conf.SMTP_USER
        and conf.SMTP_PASSWORD
        and conf.SMTP_FROM_EMAIL
    )


def _send_email_sync(to_email: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = conf.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP_SSL(conf.SMTP_HOST, conf.SMTP_PORT) as smtp:
        smtp.login(conf.SMTP_USER, conf.SMTP_PASSWORD)
        smtp.send_message(msg)


async def send_order_status_email(
    *,
    to_email: Optional[str],
    order_id: int,
    old_status: Optional[str],
    new_status: str,
) -> None:
    if not to_email or not _can_send_email() or old_status == new_status:
        return

    subject = f"Buyurtma holati yangilandi #{order_id}"
    body = (
        f"Assalomu alaykum.\n\n"
        f"Sizning buyurtmangiz holati o'zgardi.\n"
        f"Buyurtma ID: {order_id}\n"
        f"Oldingi holat: {old_status or '-'}\n"
        f"Yangi holat: {new_status}\n\n"
        f"Textile Shop"
    )

    try:
        await asyncio.to_thread(_send_email_sync, to_email, subject, body)
    except Exception as exc:
        logger.exception("Order status email yuborilmadi: order_id=%s, error=%s", order_id, exc)
