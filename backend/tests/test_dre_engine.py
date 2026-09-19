from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from app.dre.calculator import calculate
from app.dre.schemas import AdjustmentInput, PeriodInput, TransactionInput

PERIOD = PeriodInput(1, 1, 8, 2026)


def transaction(category, amount, effect, direction='OUT', **changes):
    return replace(TransactionInput(1, 1, 1, direction, category, effect, effect not in ('PENDING', 'NO_EFFECT'),
                                    'PENDING' if category == 'UNDEFINED' else 'CONFIRMED', 'CONFIRMED', 8, 2026,
                                    date(2026, 8, 10), category, Decimal(amount)), **changes)


def adjustment(kind, amount, **changes):
    return replace(AdjustmentInput(1, 1, kind, Decimal(amount), 'PENDING' if kind == 'OTHER_ADJUSTMENT' else 'CONFIRMED',
                                   'Informado explicitamente', 'PENDING' if kind == 'OTHER_ADJUSTMENT' else kind,
                                   'REVENUE_TAX' if kind == 'REVENUE_DEDUCTION' else None), **changes)


def test_financial_scenario_one():
    result, detail = calculate(PERIOD, [
        transaction('REVENUE_RECURRING', '100000', 'GROSS_REVENUE', 'IN'),
        transaction('COST', '20000', 'COST'), transaction('EXPENSE', '1500', 'OPERATING_EXPENSE'),
        transaction('INVESTMENT', '30000', 'NO_EFFECT'),
    ], [])
    assert result.net_revenue == Decimal('100000.00')
    assert result.gross_result == Decimal('80000.00')
    assert result.operating_result == result.net_result == Decimal('78500.00')
    assert result.margins.model_dump() == dict(gross=Decimal('80.00'), operating=Decimal('78.50'), net=Decimal('78.50'))
    assert result.status == 'CALCULATED'
    assert detail['costs'].count == 1


def test_financial_scenario_two():
    result, _ = calculate(PERIOD, [
        transaction('REVENUE_SERVICE', '100000', 'GROSS_REVENUE', 'IN'),
        transaction('COST', '30000', 'COST'), transaction('EXPENSE', '20000', 'OPERATING_EXPENSE'),
        transaction('FINANCIAL_REVENUE', '2000', 'FINANCIAL_REVENUE', 'IN'),
        transaction('FINANCIAL_EXPENSE', '1000', 'FINANCIAL_EXPENSE'),
    ], [adjustment('REVENUE_DEDUCTION', '10000'), adjustment('PROFIT_TAX', '5000')])
    expected = dict(gross_revenue='100000', revenue_deductions='10000', net_revenue='90000', costs='30000',
                    gross_result='60000', operating_expenses='20000', operating_result='40000', financial_revenue='2000',
                    financial_expense='1000', financial_result='1000', result_before_tax='41000', profit_taxes='5000', net_result='36000')
    for line, amount in expected.items():
        assert getattr(result, line) == Decimal(amount)
    assert result.margins.model_dump() == dict(gross=Decimal('66.67'), operating=Decimal('44.44'), net=Decimal('40.00'))


@pytest.mark.parametrize('category,direction,amount', [('INVESTMENT', 'OUT', '30000'), ('NON_DRE', 'OUT', '50000'), ('NON_DRE', 'IN', '50000')])
def test_excluded_categories_never_change_dre(category, direction, amount):
    base = [transaction('REVENUE_PRODUCT', '100000', 'GROSS_REVENUE', 'IN')]
    expected, _ = calculate(PERIOD, base, [])
    result, _ = calculate(PERIOD, base + [transaction(category, amount, 'NO_EFFECT', direction, include_in_dre=True)], [])
    assert result == expected


def test_competence_not_date_or_source_period():
    item = transaction('REVENUE_RECURRING', '100000', 'GROSS_REVENUE', 'IN', period_id=2, transaction_date=date(2026, 9, 5))
    august, _ = calculate(PERIOD, [item], [])
    september, _ = calculate(replace(PERIOD, id=2, month=9), [item], [])
    assert august.gross_revenue == Decimal('100000')
    assert september.gross_revenue == 0
    assert september.margins.net is None
    other_company, _ = calculate(replace(PERIOD, company_id=2), [item], [])
    assert other_company.gross_revenue == 0


@pytest.mark.parametrize('deduction', ['0', '100', '101'])
def test_zero_or_negative_revenue_has_null_margins(deduction):
    transactions = [] if deduction == '0' else [transaction('REVENUE_SERVICE', '100', 'GROSS_REVENUE', 'IN')]
    adjustments = [] if deduction == '0' else [adjustment('REVENUE_DEDUCTION', deduction)]
    result, _ = calculate(PERIOD, transactions, adjustments)
    assert result.net_revenue <= 0
    assert result.margins.model_dump() == dict(gross=None, operating=None, net=None)


def test_pending_and_untyped_tax_do_not_enter_calculation():
    result, _ = calculate(PERIOD, [transaction('UNDEFINED', '100', 'PENDING'), transaction('TAX', '200', 'PENDING')],
                          [adjustment('OTHER_ADJUSTMENT', '999')])
    assert result.net_result == 0
    assert result.data_quality.model_dump() == dict(pending_transactions=2, pending_adjustments=1, has_pending_items=True)
    assert result.status == 'PROVISIONAL'


def test_inconsistent_stored_effect_is_pending_not_guessed():
    result, _ = calculate(PERIOD, [transaction('COST', '100', 'GROSS_REVENUE')], [])
    assert result.gross_revenue == result.costs == 0
    assert result.data_quality.pending_transactions == 1


def test_decimal_exactness_and_half_up_rounding():
    result, _ = calculate(PERIOD, [transaction('REVENUE_SERVICE', '0.10', 'GROSS_REVENUE', 'IN'),
                                  transaction('REVENUE_SERVICE', '0.20', 'GROSS_REVENUE', 'IN')], [])
    assert result.gross_revenue == Decimal('0.30')
    result, _ = calculate(PERIOD, [transaction('REVENUE_SERVICE', '20000', 'GROSS_REVENUE', 'IN'), transaction('COST', '19999', 'COST')], [])
    assert result.margins.gross == Decimal('0.01')  # 0.005% -> half up
    result, _ = calculate(PERIOD, [transaction('REVENUE_SERVICE', '1.00', 'GROSS_REVENUE', 'IN'), transaction('COST', '2.55', 'COST')], [])
    assert result.net_result == Decimal('-1.55')
    assert result.margins.net == Decimal('-155.00')


def test_details_reconcile_and_group_archived_or_missing_subcategories():
    transactions = [transaction('COST', '10.10', 'COST', id=1, subcategory_id=5, subcategory_name='Infraestrutura'),
                    transaction('COST', '20.20', 'COST', id=2, subcategory_id=5, subcategory_name='Infraestrutura'),
                    transaction('COST', '0.01', 'COST', id=3)]
    result, details = calculate(PERIOD, transactions, [adjustment('PROFIT_TAX', '2.50')])
    for line, detail in details.items():
        assert detail.total == getattr(result, line)
        assert sum((g.total for g in detail.groups), Decimal(0)) == detail.total
        assert sum((item.amount for item in detail.items), Decimal(0)) == detail.total
        assert detail.transaction_count + detail.adjustment_count == detail.count
    assert details['costs'].groups[0].total == Decimal('30.30')
    assert details['costs'].groups[0].count == 2
    assert details['profit_taxes'].items[0].source_type == 'ADJUSTMENT'


def test_large_amounts_keep_cents_and_other_period_adjustment_is_ignored():
    result, _ = calculate(PERIOD, [transaction('REVENUE_SERVICE', '999999999999.99', 'GROSS_REVENUE', 'IN'),
                                  transaction('REVENUE_SERVICE', '0.02', 'GROSS_REVENUE', 'IN')],
                          [adjustment('PROFIT_TAX', '100', period_id=2)])
    assert result.gross_revenue == Decimal('1000000000000.01')
    assert result.profit_taxes == 0


def test_same_month_different_year_is_excluded():
    result, _ = calculate(PERIOD, [transaction('REVENUE_SERVICE', '100', 'GROSS_REVENUE', 'IN', competence_year=2025)], [])
    assert result.gross_revenue == 0
    assert result.status == 'CALCULATED'
