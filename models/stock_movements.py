"""Stock movements model for warehouse tracking."""
from enum import Enum
from sqlalchemy import BigInteger, String, Integer, Text, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from models.database import CreatedBaseModel


class StockMovement(CreatedBaseModel):
    """Ombor harakatlari - kirim, chiqim, tuzatish"""

    class MovementType(str, Enum):
        IN = "kirim"  # Ombor kirim
        OUT = "chiqim"  # Ombor chiqim
        ADJUSTMENT = "tuzatish"  # Inventarizatsiya tuzatish

    class Reason(str, Enum):
        PURCHASE = "xarid"  # Yetkazuvchidan xarid
        SALE = "sotuv"  # Mijozga sotuv
        RETURN = "qaytarish"  # Qaytarilgan mahsulot
        DAMAGE = "buzilgan"  # Buzilgan/yaroqsiz
        CORRECTION = "tuzatish"  # Inventarizatsiya tuzatish
        INITIAL = "boshlangich"  # Boshlang'ich qoldiq

    product_item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("product_items.id", ondelete="CASCADE"),
        index=True
    )
    movement_type: Mapped[str] = mapped_column(String(20), index=True)
    quantity: Mapped[int] = mapped_column(Integer)  # Musbat yoki manfiy
    reason: Mapped[str] = mapped_column(String(50), index=True)
    reference_id: Mapped[int] = mapped_column(BigInteger, nullable=True)  # order_id yoki boshqa
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    product_item: Mapped['ProductItems'] = relationship('ProductItems', lazy='selectin')
    admin_user: Mapped['AdminUser'] = relationship('AdminUser', lazy='selectin')
