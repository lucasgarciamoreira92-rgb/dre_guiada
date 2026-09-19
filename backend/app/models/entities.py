from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def now():
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_company_name"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[str | None] = mapped_column(String(18))
    segment: Mapped[str | None] = mapped_column(String(120))
    currency: Mapped[str] = mapped_column(
        String(3), default="BRL", server_default="BRL"
    )
    guided_mode: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )
    periods: Mapped[list["Period"]] = relationship(back_populates="company")


class Period(Base):
    __tablename__ = "periods"
    __table_args__ = (
        Index("uq_period_id_company", "id", "company_id", unique=True),
        UniqueConstraint(
            "company_id", "month", "year", name="uq_period_company_month_year"
        ),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_period_month"),
        CheckConstraint("year BETWEEN 1900 AND 2100", name="ck_period_year"),
        CheckConstraint(
            "completion_percentage BETWEEN 0 AND 100", name="ck_period_completion"
        ),
        CheckConstraint(
            "status IN ('draft','provisional','ready','closed','reopened')",
            name="ck_period_status",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", server_default="draft"
    )
    completion_percentage: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    company: Mapped[Company] = relationship(back_populates="periods")
