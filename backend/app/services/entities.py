from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.models.entities import Company, Period


def get_company(db, company_id):
    company = db.get(Company, company_id)
    if company is None:
        raise AppError("COMPANY_NOT_FOUND", "Empresa não encontrada.", 404)
    return company


def get_period(db, period_id):
    period = db.get(Period, period_id)
    if period is None:
        raise AppError("PERIOD_NOT_FOUND", "Período não encontrado.", 404)
    return period


def save(db, entity):
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def create_period(db, company_id, payload):
    get_company(db, company_id)
    period = Period(company_id=company_id, **payload.model_dump())
    try:
        return save(db, period)
    except IntegrityError:
        db.rollback()
        duplicate = db.scalar(
            select(Period).where(
                Period.company_id == company_id,
                Period.month == payload.month,
                Period.year == payload.year,
            )
        )
        if duplicate:
            raise AppError(
                "PERIOD_ALREADY_EXISTS",
                "Já existe um período de DRE para esta empresa neste mês e ano.",
                409,
            )
        raise
