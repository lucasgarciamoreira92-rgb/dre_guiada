from decimal import Decimal
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def periods(client):
    company = client.post('/companies', json={'name': 'Empresa Teste DRE'}).json()['data']['id']
    ids = [client.post(f'/companies/{company}/periods', json={'month': m, 'year': 2026}).json()['data']['id'] for m in (8, 9)]
    return company, *ids


def post_transaction(client, period, **changes):
    payload = dict(direction='IN', transaction_date='2026-09-05', competence_month=8, competence_year=2026,
                   description='Mensalidades', amount='100000', main_category='REVENUE_RECURRING') | changes
    response = client.post(f'/periods/{period}/transactions', json=payload)
    assert response.status_code == 201, response.text
    return response.json()['data']


def post_adjustment(client, period, **changes):
    return client.post(f'/periods/{period}/adjustments', json=dict(type='PROFIT_TAX', amount='5000', observation='Apuração informada pelo usuário') | changes)


def test_dre_endpoint_competence_and_company_isolation(client, periods):
    company, august, september = periods
    item = post_transaction(client, september)
    other = client.post('/companies', json={'name': 'Outra'}).json()['data']['id']
    other_period = client.post(f'/companies/{other}/periods', json={'month': 8, 'year': 2026}).json()['data']['id']
    post_transaction(client, other_period, amount='999999')
    data = client.get(f'/periods/{august}/dre').json()['data']
    assert data['period'] == dict(id=august, company_id=company, month=8, year=2026, status='draft')
    assert data['gross_revenue'] == '100000.00'
    assert data['status'] == 'CALCULATED'
    assert client.get(f'/periods/{september}/dre').json()['data']['gross_revenue'] == '0.00'
    detail = client.get(f'/periods/{august}/dre/gross_revenue/details').json()['data']
    assert detail['total'] == data['gross_revenue']
    assert detail['items'][0]['id'] == item['id']
    assert detail['items'][0]['period_id'] == september
    assert detail['items'][0]['transaction_date'] == '2026-09-05'
    assert client.get(f'/periods/{august}').json()['data']['status'] == 'draft'


def test_scenario_two_through_public_api_and_details(client, periods):
    _, august, _ = periods
    for changes in [{}, {'direction': 'OUT', 'main_category': 'COST', 'amount': '30000'},
                    {'direction': 'OUT', 'main_category': 'EXPENSE', 'amount': '20000'},
                    {'main_category': 'FINANCIAL_REVENUE', 'amount': '2000'},
                    {'direction': 'OUT', 'main_category': 'FINANCIAL_EXPENSE', 'amount': '1000'}]:
        post_transaction(client, august, **changes)
    assert post_adjustment(client, august).status_code == 201
    r = post_adjustment(client, august, type='REVENUE_DEDUCTION', deduction_kind='REVENUE_TAX', amount='10000')
    assert r.status_code == 201
    assert r.json()['data']['dre_effect'] == 'REVENUE_DEDUCTION'
    data = client.get(f'/periods/{august}/dre').json()['data']
    assert data['net_result'] == '36000.00'
    assert data['margins'] == dict(gross='66.67', operating='44.44', net='40.00')
    for line in ['gross_revenue','revenue_deductions','costs','operating_expenses','financial_revenue','financial_expense','profit_taxes']:
        detail = client.get(f'/periods/{august}/dre/{line}/details').json()['data']
        assert detail['total'] == data[line]
        assert detail['count'] == 1
    adjustments = client.get(f'/periods/{august}/adjustments').json()['data']
    assert len(adjustments) == 2
    assert all(a['observation'] and a['created_at'] and a['status'] == 'CONFIRMED' for a in adjustments)


@pytest.mark.parametrize('kind', ['REVENUE_TAX', 'RETURN', 'DISCOUNT', 'OTHER_APPROVED'])
def test_explicit_deductions(client, periods, kind):
    _, august, _ = periods
    response = post_adjustment(client, august, type='REVENUE_DEDUCTION', deduction_kind=kind, amount='0.10')
    assert response.status_code == 201
    assert client.get(f'/periods/{august}/dre').json()['data']['revenue_deductions'] == '0.10'


@pytest.mark.parametrize('changes', [
    {'amount': '0'}, {'amount': '-1'}, {'amount': '1.234'}, {'amount': 'NaN'}, {'amount': '1000000000000'},
    {'type': 'INVALID'}, {'observation': ' '}, {'type': 'REVENUE_DEDUCTION'},
    {'deduction_kind': 'RETURN'}, {'type': 'REVENUE_DEDUCTION', 'deduction_kind': 'INVALID'},
    {'status': 'CONFIRMED'}, {'dre_effect': 'GROSS_REVENUE'}, {'period_id': 999},
])
def test_invalid_adjustments(client, periods, changes):
    assert post_adjustment(client, periods[1], **changes).status_code == 422
    assert client.get(f'/periods/{periods[1]}/adjustments').json()['data'] == []


def test_pending_no_effect_and_zero_revenue(client, periods):
    _, august, _ = periods
    for category in ('INVESTMENT', 'NON_DRE', 'UNDEFINED', 'TAX'):
        post_transaction(client, august, direction='OUT', main_category=category, amount='30000')
    post_adjustment(client, august, type='OTHER_ADJUSTMENT')
    data = client.get(f'/periods/{august}/dre').json()['data']
    assert data['net_result'] == '0.00'
    assert data['data_quality'] == dict(pending_transactions=2, pending_adjustments=1, has_pending_items=True)
    assert data['status'] == 'PROVISIONAL'
    assert data['margins'] == dict(gross=None, operating=None, net=None)


def test_missing_period_and_invalid_line(client):
    for suffix in ('dre', 'dre/costs/details', 'adjustments'):
        response = client.get('/periods/999/' + suffix)
        assert response.status_code == 404
        assert response.json()['error']['message'] == 'Período não encontrado.'
    assert post_adjustment(client, 999).status_code == 404
    assert client.get('/periods/999/dre/invalid/details').status_code == 422


def test_archived_subcategory_still_reconciles(client, periods):
    company, august, _ = periods
    sub = client.get(f'/companies/{company}/subcategories?main_category=COST').json()['data'][0]
    post_transaction(client, august, direction='OUT', main_category='COST', amount='10.01', subcategory_id=sub['id'])
    client.post(f"/subcategories/{sub['id']}/archive")
    detail = client.get(f'/periods/{august}/dre/costs/details').json()['data']
    assert detail['groups'] == [dict(subcategory_id=sub['id'], name=sub['name'], total='10.01', count=1)]


def test_adjustment_storage_constraints_and_closed_period(client, periods, migrated):
    _, august, _ = periods
    assert post_adjustment(client, august, amount='0.01').status_code == 201
    engine, _ = migrated
    with engine.connect() as c:
        assert c.execute(text('SELECT amount FROM period_adjustments')).scalar_one() == 1
    for sql in ["UPDATE period_adjustments SET period_id=999", "UPDATE period_adjustments SET amount=0",
                "UPDATE period_adjustments SET type='TAX'", "UPDATE period_adjustments SET dre_effect='PENDING'",
                "UPDATE period_adjustments SET observation=''", "UPDATE period_adjustments SET deduction_kind='RETURN'"]:
        with engine.begin() as c:
            with pytest.raises(IntegrityError):
                c.execute(text(sql))
    with engine.begin() as c:
        c.execute(text("UPDATE periods SET status='closed' WHERE id=:id"), {'id': august})
    assert post_adjustment(client, august).status_code == 409
    assert client.get(f'/periods/{august}/dre').status_code == 200


def test_recalculation_after_edit_and_delete(client, periods):
    item = post_transaction(client, periods[1], amount='0.10')
    client.patch(f"/transactions/{item['id']}", json={'amount': '0.20'})
    assert client.get(f'/periods/{periods[1]}/dre').json()['data']['gross_revenue'] == '0.20'
    client.delete(f"/transactions/{item['id']}")
    assert Decimal(client.get(f'/periods/{periods[1]}/dre').json()['data']['net_result']) == 0
