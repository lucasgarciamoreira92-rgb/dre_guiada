from decimal import Decimal
from app.dre.rules import ADJUSTMENT_EFFECTS, DEDUCTION_LABELS, EFFECTS
from app.dre.schemas import AdjustmentInput, PeriodInput, TransactionInput


def in_competence(period: PeriodInput, item: TransactionInput) -> bool:
    return (item.company_id, item.competence_month, item.competence_year) == (period.company_id, period.month, period.year)


def valid_amount(amount: Decimal) -> bool:
    return isinstance(amount, Decimal) and amount.is_finite() and amount > 0


def transaction_pending(item: TransactionInput) -> bool:
    expected = EFFECTS.get(item.direction, {}).get(item.main_category)
    return (item.main_category == 'UNDEFINED' or item.dre_effect == 'PENDING'
            or expected is None or expected != item.dre_effect
            or item.classification_status != 'CONFIRMED'
            or item.competence_status != 'CONFIRMED'
            or not valid_amount(item.amount)
            or (expected != 'NO_EFFECT' and not item.include_in_dre))


def adjustment_pending(item: AdjustmentInput) -> bool:
    expected = ADJUSTMENT_EFFECTS.get(item.type)
    return (expected is None or expected == 'PENDING' or item.dre_effect != expected
            or item.status != 'CONFIRMED' or not valid_amount(item.amount)
            or (item.type == 'REVENUE_DEDUCTION' and item.deduction_kind not in DEDUCTION_LABELS))
