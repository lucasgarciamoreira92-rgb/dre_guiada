from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey,
                        ForeignKeyConstraint, Index, Numeric, String, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.core.categories import CATEGORIES, IN_EFFECTS, OUT_EFFECTS
from app.db.session import Base
from app.models.entities import now


def sql_values(values):
    return ','.join(repr(v) for v in values)


class Money(TypeDecorator):
    """Decimal API; exact scaled integer cents on SQLite (which has no decimal type)."""
    impl = Numeric(14, 2)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(BigInteger() if dialect.name == 'sqlite' else Numeric(14, 2))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        amount = Decimal(str(value))
        if not amount.is_finite() or amount != amount.quantize(Decimal('0.01')):
            raise ValueError('Valor deve ter no máximo duas casas decimais.')
        return int(amount * 100) if dialect.name == 'sqlite' else amount

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        amount = Decimal(value) / 100 if dialect.name == 'sqlite' else Decimal(value)
        return amount.quantize(Decimal('0.01'))


class Subcategory(Base):
    __tablename__ = 'subcategories'
    __table_args__ = (
        UniqueConstraint('company_id', 'main_category', 'normalized_name', name='uq_subcategory_name'),
        UniqueConstraint('id', 'company_id', 'main_category', name='uq_subcategory_identity'),
        CheckConstraint('length(trim(name)) > 0', name='ck_subcategory_name'),
        CheckConstraint(f'main_category IN ({sql_values(CATEGORIES)})', name='ck_subcategory_category'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'), index=True)
    main_category: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    normalized_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default='1')
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default='0')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Transaction(Base):
    __tablename__ = 'transactions'
    __table_args__ = (
        ForeignKeyConstraint(['period_id', 'company_id'], ['periods.id', 'periods.company_id'], name='fk_transaction_period_company'),
        ForeignKeyConstraint(['subcategory_id', 'company_id', 'main_category'], ['subcategories.id', 'subcategories.company_id', 'subcategories.main_category'], name='fk_transaction_subcategory'),
        CheckConstraint("direction IN ('IN','OUT')", name='ck_transaction_direction'),
        CheckConstraint(f"(direction = 'IN' AND main_category IN ({sql_values(IN_EFFECTS)})) OR (direction = 'OUT' AND main_category IN ({sql_values(OUT_EFFECTS)}))", name='ck_transaction_category'),
        CheckConstraint('amount > 0 AND amount <= 99999999999999', name='ck_transaction_amount'),
        CheckConstraint('competence_month BETWEEN 1 AND 12', name='ck_transaction_month'),
        CheckConstraint('competence_year BETWEEN 1900 AND 2100', name='ck_transaction_year'),
        CheckConstraint('length(trim(description)) > 0', name='ck_transaction_description'),
        CheckConstraint("origin_type = 'MANUAL' AND competence_source = 'USER' AND competence_status = 'CONFIRMED'", name='ck_transaction_manual'),
        CheckConstraint("classification_status IN ('PENDING','CONFIRMED')", name='ck_transaction_classification'),
        CheckConstraint("dre_effect IN ('GROSS_REVENUE','COST','OPERATING_EXPENSE','FINANCIAL_REVENUE','FINANCIAL_EXPENSE','NO_EFFECT','PENDING')", name='ck_transaction_effect'),
        Index('ix_transactions_period_direction', 'period_id', 'direction'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'), index=True)
    period_id: Mapped[int] = mapped_column()
    direction: Mapped[str] = mapped_column(String(3))
    transaction_date: Mapped[date] = mapped_column(Date)
    competence_month: Mapped[int] = mapped_column()
    competence_year: Mapped[int] = mapped_column()
    competence_status: Mapped[str] = mapped_column(String(20), default='CONFIRMED')
    competence_source: Mapped[str] = mapped_column(String(20), default='USER')
    description: Mapped[str] = mapped_column(String(500))
    original_description: Mapped[str] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(Money())
    main_category: Mapped[str] = mapped_column(String(40))
    subcategory_id: Mapped[int | None] = mapped_column(index=True)
    dre_effect: Mapped[str] = mapped_column(String(30))
    classification_status: Mapped[str] = mapped_column(String(20))
    include_in_dre: Mapped[bool] = mapped_column(Boolean)
    observation: Mapped[str | None] = mapped_column(String(2000))
    origin_type: Mapped[str] = mapped_column(String(20), default='MANUAL')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
