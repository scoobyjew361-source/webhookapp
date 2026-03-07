from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcessedUpdate(Base):
    __tablename__ = "processed_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    update_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
