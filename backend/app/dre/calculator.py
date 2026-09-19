"""Pure deterministic calculation. Reads no database and writes no period state."""
from dataclasses import asdict
from decimal import localcontext

from app.dre.rules import DEDUCTION_LABELS, EFFECT_LINES, ZERO, margin, rounded
from app.dre.schemas import (AdjustmentInput, DataQuality, DetailGroup, DetailItem,
                             DetailsRead, DreRead, Margins, PeriodInput, TransactionInput)
from app.dre.validator import adjustment_pending, in_competence, transaction_pending


def calculate(period: PeriodInput, transactions: list[TransactionInput], adjustments: list[AdjustmentInput]):
    with localcontext() as context:
        context.prec = 40
        items = {line: [] for line in EFFECT_LINES.values()}
        groups = {line: {} for line in EFFECT_LINES.values()}
        pending_transactions = pending_adjustments = 0

        def append(line, item, group_id, group_name):
            items[line].append(item)
            key = (group_id, group_name)
            group = groups[line].setdefault(key, dict(subcategory_id=group_id, name=group_name, total=ZERO, count=0))
            group['total'] += item.amount
            group['count'] += 1

        for item in transactions:
            if not in_competence(period, item):
                continue
            if transaction_pending(item):
                pending_transactions += 1
                continue
            # NO_EFFECT never contributes, even when an inconsistent include flag is true.
            if item.dre_effect == 'NO_EFFECT':
                continue
            line = EFFECT_LINES[item.dre_effect]
            append(line, DetailItem(source_type='TRANSACTION', id=item.id, period_id=item.period_id,
                                   direction=item.direction, description=item.description, amount=item.amount,
                                   transaction_date=item.transaction_date, competence_month=item.competence_month,
                                   competence_year=item.competence_year),
                   item.subcategory_id, item.subcategory_name or 'Sem subcategoria')

        for item in adjustments:
            if item.period_id != period.id:
                continue
            if adjustment_pending(item):
                pending_adjustments += 1
                continue
            line = EFFECT_LINES[item.dre_effect]
            label = DEDUCTION_LABELS[item.deduction_kind] if item.type == 'REVENUE_DEDUCTION' else 'Tributos sobre lucro'
            append(line, DetailItem(source_type='ADJUSTMENT', id=item.id, period_id=item.period_id,
                                   description=item.observation, amount=item.amount,
                                   competence_month=period.month, competence_year=period.year), None, label)

        totals = {line: rounded(sum((item.amount for item in entries), ZERO)) for line, entries in items.items()}
        net_revenue = totals['gross_revenue'] - totals['revenue_deductions']
        gross_result = net_revenue - totals['costs']
        operating_result = gross_result - totals['operating_expenses']
        financial_result = totals['financial_revenue'] - totals['financial_expense']
        result_before_tax = operating_result + financial_result
        net_result = result_before_tax - totals['profit_taxes']
        has_pending = bool(pending_transactions or pending_adjustments)
        result = DreRead(
            period=asdict(period), status='PROVISIONAL' if has_pending else 'CALCULATED', **totals,
            net_revenue=net_revenue, gross_result=gross_result, operating_result=operating_result,
            financial_result=financial_result, result_before_tax=result_before_tax, net_result=net_result,
            margins=Margins(gross=margin(gross_result, net_revenue), operating=margin(operating_result, net_revenue), net=margin(net_result, net_revenue)),
            data_quality=DataQuality(pending_transactions=pending_transactions, pending_adjustments=pending_adjustments, has_pending_items=has_pending),
        )
        details = {
            line: DetailsRead(line=line, total=totals[line], count=len(entries),
                              transaction_count=sum(item.source_type == 'TRANSACTION' for item in entries),
                              adjustment_count=sum(item.source_type == 'ADJUSTMENT' for item in entries),
                              groups=[DetailGroup(**group) for group in groups[line].values()], items=entries)
            for line, entries in items.items()
        }
        return result, details
