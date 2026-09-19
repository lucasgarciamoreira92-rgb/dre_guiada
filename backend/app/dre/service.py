from dataclasses import fields
from sqlalchemy import select

from app.dre.calculator import calculate
from app.dre.rules import ADJUSTMENT_EFFECTS
from app.dre.schemas import AdjustmentInput, PeriodInput, TransactionInput
from app.models.adjustments import PeriodAdjustment
from app.models.manual import Subcategory, Transaction
from app.services.entities import get_period, save
from app.services.manual import ensure_open


def calculate_period(db, period_id):
    period = get_period(db, period_id)
    # The source period_id is deliberately not a filter: competence controls the DRE.
    rows = db.execute(select(Transaction, Subcategory.name).outerjoin(Subcategory, Transaction.subcategory_id == Subcategory.id)
                      .where(Transaction.company_id == period.company_id,
                             Transaction.competence_month == period.month,
                             Transaction.competence_year == period.year).order_by(Transaction.id)).all()
    transactions = [TransactionInput(**{f.name: getattr(item, f.name) for f in fields(TransactionInput) if f.name != 'subcategory_name'}, subcategory_name=name)
                    for item, name in rows]
    adjustments = [AdjustmentInput(**{f.name: getattr(item, f.name) for f in fields(AdjustmentInput)}) for item in list_adjustments(db, period_id)]
    return calculate(PeriodInput(period.id, period.company_id, period.month, period.year, period.status), transactions, adjustments)


def list_adjustments(db, period_id):
    get_period(db, period_id)
    return db.scalars(select(PeriodAdjustment).where(PeriodAdjustment.period_id == period_id).order_by(PeriodAdjustment.id)).all()


def create_adjustment(db, period_id, payload):
    ensure_open(get_period(db, period_id))
    effect = ADJUSTMENT_EFFECTS[payload.type]
    return save(db, PeriodAdjustment(period_id=period_id, **payload.model_dump(), dre_effect=effect,
                                    status='PENDING' if effect == 'PENDING' else 'CONFIRMED'))
