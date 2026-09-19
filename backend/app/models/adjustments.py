from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.entities import now
from app.models.manual import Money


class PeriodAdjustment(Base):
    __tablename__ = 'period_adjustments'
    __table_args__ = (
        CheckConstraint("type IN ('PROFIT_TAX','OTHER_ADJUSTMENT','REVENUE_DEDUCTION')", name='ck_adjustment_type'),
        CheckConstraint('amount > 0 AND amount <= 99999999999999', name='ck_adjustment_amount'),
        CheckConstraint('length(trim(observation)) > 0', name='ck_adjustment_observation'),
        CheckConstraint("(type = 'PROFIT_TAX' AND status = 'CONFIRMED' AND dre_effect = 'PROFIT_TAX' AND deduction_kind IS NULL) OR "
                        "(type = 'OTHER_ADJUSTMENT' AND status = 'PENDING' AND dre_effect = 'PENDING' AND deduction_kind IS NULL) OR "
                        "(type = 'REVENUE_DEDUCTION' AND status = 'CONFIRMED' AND dre_effect = 'REVENUE_DEDUCTION' AND deduction_kind IS NOT NULL AND "
                        "deduction_kind IN ('REVENUE_TAX','RETURN','DISCOUNT','OTHER_APPROVED'))", name='ck_adjustment_rule'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey('periods.id'), index=True)
    type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Money())
    status: Mapped[str] = mapped_column(String(20))
    observation: Mapped[str] = mapped_column(String(2000))
    dre_effect: Mapped[str] = mapped_column(String(30))
    deduction_kind: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
