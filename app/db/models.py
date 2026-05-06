from __future__ import annotations

from uuid import uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.intervals import MINUTES_PER_WEEK


def _default_id() -> str:
    return str(uuid4())


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_default_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    opening_intervals: Mapped[list["OpeningIntervalModel"]] = relationship(
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )


class OpeningIntervalModel(Base):
    __tablename__ = "opening_intervals"
    __table_args__ = (
        CheckConstraint("start_minute >= 0", name="ck_opening_intervals_start_minute_min"),
        CheckConstraint(
            f"start_minute < {MINUTES_PER_WEEK}",
            name="ck_opening_intervals_start_minute_max",
        ),
        CheckConstraint("end_minute > 0", name="ck_opening_intervals_end_minute_min"),
        CheckConstraint(
            f"end_minute <= {MINUTES_PER_WEEK}",
            name="ck_opening_intervals_end_minute_max",
        ),
        CheckConstraint(
            "start_minute < end_minute",
            name="ck_opening_intervals_start_before_end",
        ),
        Index(
            "ix_opening_intervals_restaurant_id_start_end",
            "restaurant_id",
            "start_minute",
            "end_minute",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_default_id)
    restaurant_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_minute: Mapped[int] = mapped_column(nullable=False)
    end_minute: Mapped[int] = mapped_column(nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="opening_intervals")


__all__ = ["Base", "OpeningIntervalModel", "Restaurant"]
