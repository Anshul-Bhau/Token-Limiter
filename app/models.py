from datetime import datetime, timezone

from sqlalchemy import String, Float, Integer, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class AlgorithmType(str, enum.Enum):
    token_bucket = "token_bucket"
    sliding_window = "sliding_window"

class ClientConfig(Base):
    __tablename__ = "client_config"

    client_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    max_tokens: Mapped[int] = mapped_column(Integer, default=10)
    refill_rate: Mapped[float] = mapped_column(Float, default=2.0)
    window_size: Mapped[int] = mapped_column(Integer, default=60)
    algorithm: Mapped[str] = mapped_column(
        Enum(AlgorithmType), default=AlgorithmType.token_bucket
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default= lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class RequestStats(Base):
    # Flushed from Redis counters periodically (background task)
    __tablename__ = "request_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_key: Mapped[str] = mapped_column(String(255), index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total: Mapped[int] = mapped_column(Integer, default=0)
    allowed: Mapped[int] = mapped_column(Integer, default=0)
    denied: Mapped[int] = mapped_column(Integer, default=0)

    