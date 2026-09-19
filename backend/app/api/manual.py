from fastapi import APIRouter
from sqlalchemy import select
from app.api.routes import DB
from app.models.manual import Subcategory
from app.schemas.manual import (Category, TransactionCreate, TransactionPatch, TransactionResponse,
                                TransactionsResponse, SubcategoryCreate, SubcategoryPatch,
                                SubcategoryResponse, SubcategoriesResponse)
from app.services import manual as service
from app.services.entities import get_company, get_period, save

router = APIRouter()


@router.post('/periods/{period_id}/transactions', response_model=TransactionResponse, status_code=201)
def create_transaction(period_id: int, payload: TransactionCreate, db: DB):
    return {'data': service.create_transaction(db, period_id, payload)}


@router.get('/periods/{period_id}/revenues', response_model=TransactionsResponse)
def revenues(period_id: int, db: DB):
    return {'data': service.list_transactions(db, period_id, 'IN')}


@router.get('/periods/{period_id}/expenses', response_model=TransactionsResponse)
def expenses(period_id: int, db: DB):
    return {'data': service.list_transactions(db, period_id, 'OUT')}


@router.get('/transactions/{transaction_id}', response_model=TransactionResponse)
def transaction(transaction_id: int, db: DB):
    return {'data': service.get_transaction(db, transaction_id)}


@router.patch('/transactions/{transaction_id}', response_model=TransactionResponse)
def patch_transaction(transaction_id: int, payload: TransactionPatch, db: DB):
    return {'data': service.patch_transaction(db, service.get_transaction(db, transaction_id), payload)}


@router.delete('/transactions/{transaction_id}')
def delete_transaction(transaction_id: int, db: DB):
    item = service.get_transaction(db, transaction_id)
    service.ensure_open(get_period(db, item.period_id))
    db.delete(item)
    db.commit()
    return {'data': {'deleted': True}}


@router.get('/companies/{company_id}/subcategories', response_model=SubcategoriesResponse)
def subcategories(company_id: int, db: DB, main_category: Category | None = None):
    get_company(db, company_id)
    query = select(Subcategory).where(Subcategory.company_id == company_id)
    if main_category:
        query = query.where(Subcategory.main_category == main_category)
    return {'data': db.scalars(query.order_by(Subcategory.main_category, Subcategory.id)).all()}


@router.post('/companies/{company_id}/subcategories', response_model=SubcategoryResponse, status_code=201)
def create_subcategory(company_id: int, payload: SubcategoryCreate, db: DB):
    return {'data': service.create_subcategory(db, company_id, payload)}


@router.patch('/subcategories/{subcategory_id}', response_model=SubcategoryResponse)
def patch_subcategory(subcategory_id: int, payload: SubcategoryPatch, db: DB):
    return {'data': service.patch_subcategory(db, service.get_subcategory(db, subcategory_id), payload)}


@router.post('/subcategories/{subcategory_id}/archive', response_model=SubcategoryResponse)
def archive_subcategory(subcategory_id: int, db: DB):
    item = service.get_subcategory(db, subcategory_id)
    item.active = False
    return {'data': save(db, item)}
