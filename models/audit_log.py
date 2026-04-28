from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.database import CreatedBaseModel


class AuditLog(CreatedBaseModel):
    entity: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(128), default="system")
    details: Mapped[str] = mapped_column(Text, default="")
