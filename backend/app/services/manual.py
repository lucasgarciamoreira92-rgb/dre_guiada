from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.categories import DEFAULT_SUBCATEGORIES, EFFECTS
from app.core.errors import AppError
from app.models.manual import Subcategory, Transaction
from app.services.entities import get_company, get_period, save


def seed_subcategories(db, company_id):
    for category, names in DEFAULT_SUBCATEGORIES.items():
        for name in names:
            db.add(Subcategory(company_id=company_id, main_category=category,
                               name=name, normalized_name=name.casefold(), is_default=True))


def get_transaction(db, transaction_id):
    item = db.get(Transaction, transaction_id)
    if item is None:
        raise AppError('TRANSACTION_NOT_FOUND', 'Lançamento não encontrado.', 404)
    return item


def get_subcategory(db, subcategory_id):
    item = db.get(Subcategory, subcategory_id)
    if item is None:
        raise AppError('SUBCATEGORY_NOT_FOUND', 'Subcategoria não encontrada.', 404)
    return item


def ensure_open(period):
    if period.status == 'closed':
        raise AppError('PERIOD_CLOSED', 'Este período está fechado e não pode ser alterado.', 409)


def classify(direction, category):
    if category not in EFFECTS[direction]:
        raise AppError('INCOMPATIBLE_CATEGORY', 'A categoria não é compatível com receita ou saída.', 422)
    effect = EFFECTS[direction][category]
    return dict(dre_effect=effect, classification_status='PENDING' if category == 'UNDEFINED' else 'CONFIRMED',
                include_in_dre=effect not in ('NO_EFFECT', 'PENDING'))


def validate_subcategory(db, subcategory_id, company_id, category, previous_id=None):
    if subcategory_id is None:
        return
    sub = get_subcategory(db, subcategory_id)
    if sub.company_id != company_id:
        raise AppError('SUBCATEGORY_COMPANY_MISMATCH', 'A subcategoria pertence a outra empresa.', 422)
    if sub.main_category != category:
        raise AppError('SUBCATEGORY_CATEGORY_MISMATCH', 'Escolha uma subcategoria da categoria selecionada.', 422)
    if not sub.active and subcategory_id != previous_id:
        raise AppError('SUBCATEGORY_ARCHIVED', 'Esta subcategoria está arquivada. Escolha outra.', 422)


def create_transaction(db, period_id, payload):
    period = get_period(db, period_id)
    ensure_open(period)
    data = payload.model_dump()
    derived = classify(data['direction'], data['main_category'])
    validate_subcategory(db, data['subcategory_id'], period.company_id, data['main_category'])
    return save(db, Transaction(company_id=period.company_id, period_id=period.id,
                               original_description=data['description'], **data, **derived))


def patch_transaction(db, item, payload):
    ensure_open(get_period(db, item.period_id))
    changes = payload.model_dump(exclude_unset=True)
    category = changes.get('main_category', item.main_category)
    derived = classify(item.direction, category)
    sub_id = changes.get('subcategory_id', item.subcategory_id)
    validate_subcategory(db, sub_id, item.company_id, category, item.subcategory_id)
    for key, value in {**changes, **derived}.items():
        setattr(item, key, value)
    return save(db, item)


def list_transactions(db, period_id, direction):
    get_period(db, period_id)
    return db.scalars(select(Transaction).where(Transaction.period_id == period_id, Transaction.direction == direction)
                      .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())).all()


def save_subcategory(db, item):
    item.normalized_name = ' '.join(item.name.split()).casefold()
    item.name = ' '.join(item.name.split())
    try:
        return save(db, item)
    except IntegrityError:
        db.rollback()
        raise AppError('SUBCATEGORY_ALREADY_EXISTS', 'Já existe uma subcategoria com esse nome nesta categoria, inclusive arquivadas.', 409)


def create_subcategory(db, company_id, payload):
    get_company(db, company_id)
    return save_subcategory(db, Subcategory(company_id=company_id, **payload.model_dump()))


def patch_subcategory(db, item, payload):
    if item.is_default:
        raise AppError('DEFAULT_SUBCATEGORY', 'Subcategorias padrão não podem ser editadas. Crie uma personalizada.', 409)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get('main_category', item.main_category) != item.main_category:
        if db.scalar(select(Transaction.id).where(Transaction.subcategory_id == item.id).limit(1)):
            raise AppError('SUBCATEGORY_IN_USE', 'Esta subcategoria já possui lançamentos. Crie outra para mudar a categoria.', 409)
    for key, value in changes.items():
        setattr(item, key, value)
    return save_subcategory(db, item)
