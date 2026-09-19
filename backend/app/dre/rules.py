"""Explicit rules only; no tax inference or financial calculations in the client."""
from decimal import Decimal, ROUND_HALF_UP
from app.core.categories import EFFECTS

CENT = Decimal('0.01')
ZERO = Decimal('0.00')
EFFECT_LINES = {
    'GROSS_REVENUE': 'gross_revenue',
    'REVENUE_DEDUCTION': 'revenue_deductions',
    'COST': 'costs',
    'OPERATING_EXPENSE': 'operating_expenses',
    'FINANCIAL_REVENUE': 'financial_revenue',
    'FINANCIAL_EXPENSE': 'financial_expense',
    'PROFIT_TAX': 'profit_taxes',
}
ADJUSTMENT_EFFECTS = {
    'PROFIT_TAX': 'PROFIT_TAX',
    'REVENUE_DEDUCTION': 'REVENUE_DEDUCTION',
    'OTHER_ADJUSTMENT': 'PENDING',
}
DEDUCTION_LABELS = {
    'REVENUE_TAX': 'Impostos sobre receita',
    'RETURN': 'Devoluções',
    'DISCOUNT': 'Abatimentos',
    'OTHER_APPROVED': 'Outras deduções aprovadas',
}


def rounded(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def margin(result: Decimal, net_revenue: Decimal) -> Decimal | None:
    return rounded(result / net_revenue * Decimal(100)) if net_revenue > ZERO else None
