from decimal import Decimal
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def context(client):
    company = client.post('/companies', json={'name': 'Empresa Teste DRE'}).json()['data']
    period = client.post(f"/companies/{company['id']}/periods", json={'month': 8, 'year': 2026}).json()['data']
    return company['id'], period['id']


def payload(**changes):
    return dict(direction='IN', transaction_date='2026-08-05', competence_month=8, competence_year=2026,
                description='Mensalidades', amount='100000.00', main_category='REVENUE_RECURRING') | changes


def create(client, context, **changes):
    return client.post(f'/periods/{context[1]}/transactions', json=payload(**changes))


def test_transaction_crud_and_direction_lists(client, context):
    r = create(client, context)
    assert r.status_code == 201
    item = r.json()['data']
    assert item['amount'] == '100000.00'
    assert item['company_id'] == context[0]
    for field, value in dict(origin_type='MANUAL', competence_status='CONFIRMED', competence_source='USER',
                             original_description='Mensalidades', classification_status='CONFIRMED', include_in_dre=True).items():
        assert item[field] == value
    path = f"/transactions/{item['id']}"
    assert client.get(path).json()['data'] == item
    out = create(client, context, direction='OUT', main_category='COST', description='Link IP', amount='20000').json()['data']
    assert [t['id'] for t in client.get(f'/periods/{context[1]}/revenues').json()['data']] == [item['id']]
    assert [t['id'] for t in client.get(f'/periods/{context[1]}/expenses').json()['data']] == [out['id']]
    edited = client.patch(path, json={'description': 'Mensalidades editadas', 'amount': '100.01', 'main_category': 'NON_DRE', 'competence_month': 9}).json()['data']
    assert edited['original_description'] == 'Mensalidades'
    assert edited['description'] == 'Mensalidades editadas'
    assert edited['amount'] == '100.01'
    assert edited['competence_month'] == 9
    assert edited['dre_effect'] == 'NO_EFFECT'
    assert edited['include_in_dre'] is False
    assert client.delete(path).json()['data']['deleted'] is True
    assert client.get(path).status_code == 404
    assert client.delete(path).status_code == 404


@pytest.mark.parametrize('direction,category,effect,classified,included', [
    ('IN', 'REVENUE_RECURRING', 'GROSS_REVENUE', 'CONFIRMED', True),
    ('IN', 'REVENUE_SERVICE', 'GROSS_REVENUE', 'CONFIRMED', True),
    ('IN', 'REVENUE_PRODUCT', 'GROSS_REVENUE', 'CONFIRMED', True),
    ('IN', 'REVENUE_OTHER_OPERATING', 'GROSS_REVENUE', 'CONFIRMED', True),
    ('IN', 'FINANCIAL_REVENUE', 'FINANCIAL_REVENUE', 'CONFIRMED', True),
    ('IN', 'NON_DRE', 'NO_EFFECT', 'CONFIRMED', False),
    ('IN', 'UNDEFINED', 'PENDING', 'PENDING', False),
    ('OUT', 'COST', 'COST', 'CONFIRMED', True),
    ('OUT', 'EXPENSE', 'OPERATING_EXPENSE', 'CONFIRMED', True),
    ('OUT', 'INVESTMENT', 'NO_EFFECT', 'CONFIRMED', False),
    ('OUT', 'FINANCIAL_EXPENSE', 'FINANCIAL_EXPENSE', 'CONFIRMED', True),
    ('OUT', 'TAX', 'PENDING', 'CONFIRMED', False),
    ('OUT', 'NON_DRE', 'NO_EFFECT', 'CONFIRMED', False),
    ('OUT', 'UNDEFINED', 'PENDING', 'PENDING', False),
])
def test_effects(client, context, direction, category, effect, classified, included):
    r = create(client, context, direction=direction, main_category=category)
    assert r.status_code == 201
    item = r.json()['data']
    assert (item['dre_effect'], item['classification_status'], item['include_in_dre']) == (effect, classified, included)


@pytest.mark.parametrize('changes', [
    {'amount': '0'}, {'amount': '-1'}, {'amount': '0.001'}, {'amount': 'NaN'}, {'amount': 'Infinity'},
    {'amount': '1000000000000'}, {'competence_month': 0}, {'competence_month': 13},
    {'competence_month': 1.2}, {'competence_year': 1800}, {'competence_year': 2101},
    {'description': '  '}, {'main_category': 'INVALID'}, {'main_category': 'COST'},
    {'direction': 'OUT', 'main_category': 'REVENUE_SERVICE'}, {'direction': 'OTHER'},
    {'transaction_date': '2026-02-30'}, {'amount': None}, {'company_id': 999}, {'period_id': 999},
    {'origin_type': 'IMPORT'}, {'dre_effect': 'COST'}, {'include_in_dre': False},
])
def test_invalid_transaction(client, context, changes):
    response = create(client, context, **changes)
    assert response.status_code == 422
    assert response.json()['error']['message']
    assert client.get(f'/periods/{context[1]}/revenues').json()['data'] == []


@pytest.mark.parametrize('field', ['amount', 'description', 'transaction_date', 'main_category', 'competence_month', 'competence_year'])
def test_patch_null_rejected(client, context, field):
    item = create(client, context).json()['data']
    assert client.patch(f"/transactions/{item['id']}", json={field: None}).status_code == 422


def test_missing_resources(client):
    assert create(client, (999, 999)).status_code == 404
    assert client.get('/periods/999/revenues').status_code == 404
    assert client.get('/periods/999/expenses').status_code == 404
    assert client.get('/transactions/999').status_code == 404
    assert client.patch('/transactions/999', json={'amount': '1'}).status_code == 404
    assert client.get('/companies/999/subcategories').status_code == 404
    assert client.post('/companies/999/subcategories', json={'name': 'Teste', 'main_category': 'COST'}).status_code == 404
    assert client.post('/subcategories/999/archive').status_code == 404


def test_subcategories_defaults_custom_edit_archive(client, context):
    base = f'/companies/{context[0]}/subcategories'
    defaults = client.get(base).json()['data']
    assert len(defaults) == 20
    assert all(s['is_default'] for s in defaults)
    assert len(client.get(base, params={'main_category': 'COST'}).json()['data']) == 5
    assert len(client.get(base).json()['data']) == 20
    r = client.post(base, json={'name': '  Meu   custo ', 'main_category': 'COST', 'description': 'Personalizada'})
    assert r.status_code == 201
    sub = r.json()['data']
    assert sub['name'] == 'Meu custo'
    path = f"/subcategories/{sub['id']}"
    assert client.post(base, json={'name': 'MEU CUSTO', 'main_category': 'COST'}).status_code == 409
    assert client.patch(path, json={'name': 'Custo especial', 'description': None}).json()['data']['name'] == 'Custo especial'
    assert client.patch(f"/subcategories/{defaults[0]['id']}", json={'name': 'Modificado'}).status_code == 409
    assert client.post(path + '/archive').json()['data']['active'] is False
    assert create(client, context, direction='OUT', main_category='COST', subcategory_id=sub['id']).status_code == 422
    assert client.post(base, json={'name': ' ', 'main_category': 'COST'}).status_code == 422


def test_subcategory_ownership_compatibility_and_history(client, context):
    base = f'/companies/{context[0]}/subcategories'
    sub = client.post(base, json={'name': 'Especial', 'main_category': 'COST'}).json()['data']
    company2 = client.post('/companies', json={'name': 'Outra'}).json()['data']['id']
    other = client.get(f'/companies/{company2}/subcategories', params={'main_category': 'COST'}).json()['data'][0]
    assert create(client, context, direction='OUT', main_category='COST', subcategory_id=other['id']).status_code == 422
    assert create(client, context, direction='OUT', main_category='EXPENSE', subcategory_id=sub['id']).status_code == 422
    item = create(client, context, direction='OUT', main_category='COST', subcategory_id=sub['id']).json()['data']
    path = f"/transactions/{item['id']}"
    assert client.patch(path, json={'main_category': 'EXPENSE'}).status_code == 422
    assert client.patch(f"/subcategories/{sub['id']}", json={'main_category': 'EXPENSE'}).status_code == 409
    assert client.post(f"/subcategories/{sub['id']}/archive").status_code == 200
    assert client.patch(path, json={'description': 'Corrigido'}).status_code == 200
    updated = client.patch(path, json={'main_category': 'EXPENSE', 'subcategory_id': None}).json()['data']
    assert updated['dre_effect'] == 'OPERATING_EXPENSE'
    assert updated['subcategory_id'] is None


def test_closed_period_and_exact_storage(client, context, migrated):
    item = create(client, context, amount='999999999999.99').json()['data']
    assert item['amount'] == '999999999999.99'
    engine, _ = migrated
    with engine.begin() as c:
        assert c.execute(text('SELECT amount FROM transactions')).scalar_one() == 99999999999999
        for field, value in [('company_id', 999), ('period_id', 999), ('amount', 0), ('direction', "'OTHER'")]:
            with pytest.raises(IntegrityError):
                c.execute(text(f'UPDATE transactions SET {field}={value}'))
        c.execute(text("UPDATE periods SET status='closed'"))
    assert create(client, context).status_code == 409
    assert client.patch(f"/transactions/{item['id']}", json={'amount': '1'}).status_code == 409
    assert client.delete(f"/transactions/{item['id']}").status_code == 409


def test_cent_values(client, context):
    for amount in ['0.01', '0.10', '0.20', '123456789012.34']:
        response = create(client, context, amount=amount)
        assert response.status_code == 201
        assert Decimal(response.json()['data']['amount']) == Decimal(amount)


def test_database_rejects_cross_company_and_category_links(client, context, migrated):
    other_company = client.post('/companies', json={'name': 'Outra empresa'}).json()['data']['id']
    other_period = client.post(f'/companies/{other_company}/periods', json={'month': 8, 'year': 2026}).json()['data']['id']
    own_sub = client.get(f'/companies/{context[0]}/subcategories', params={'main_category': 'COST'}).json()['data'][0]['id']
    other_sub = client.get(f'/companies/{other_company}/subcategories', params={'main_category': 'COST'}).json()['data'][0]['id']
    create(client, context, direction='OUT', main_category='COST', subcategory_id=own_sub)
    engine, _ = migrated
    for sql in [f'UPDATE transactions SET company_id={other_company}', f'UPDATE transactions SET period_id={other_period}',
                f'UPDATE transactions SET subcategory_id={other_sub}', "UPDATE transactions SET main_category='EXPENSE'"]:
        with engine.begin() as c:
            with pytest.raises(IntegrityError):
                c.execute(text(sql))


def test_edit_invalid_amount_keeps_record(client, context):
    item = create(client, context).json()['data']
    path = f"/transactions/{item['id']}"
    for value in ['0', '-10', '1.234']:
        assert client.patch(path, json={'amount': value}).status_code == 422
    assert client.get(path).json()['data']['amount'] == '100000.00'
