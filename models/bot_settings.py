"""Bot settings model for admin panel."""
from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import mapped_column, Mapped
from models.database import BaseModel


class BotSettings(BaseModel):
    """Telegram bot sozlamalari"""
    __tablename__ = "bot_settings"

    bot_token: Mapped[str] = mapped_column(Text, nullable=True)
    group_ids: Mapped[str] = mapped_column(Text, nullable=True)  # Comma-separated IDs
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_new_orders: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_low_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_payment: Mapped[bool] = mapped_column(Boolean, default=True)
