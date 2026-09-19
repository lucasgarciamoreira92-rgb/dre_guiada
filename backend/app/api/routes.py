from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Company, Period
from app.schemas.entities import (
    CompaniesResponse,
    CompanyCreate,
    CompanyPatch,
    CompanyResponse,
    PeriodCreate,
    PeriodResponse,
    PeriodsResponse,
)
from app.services import entities as service

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]


@router.post("/companies", response_model=CompanyResponse, status_code=201)
def create_company(payload: CompanyCreate, db: DB):
    return {"data": service.save(db, Company(**payload.model_dump()))}


@router.get("/companies", response_model=CompaniesResponse)
def list_companies(db: DB):
    return {"data": db.scalars(select(Company).order_by(Company.id)).all()}


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def read_company(company_id: int, db: DB):
    return {"data": service.get_company(db, company_id)}


@router.patch("/companies/{company_id}", response_model=CompanyResponse)
def edit_company(company_id: int, payload: CompanyPatch, db: DB):
    company = service.get_company(db, company_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    return {"data": service.save(db, company)}


@router.post(
    "/companies/{company_id}/periods", response_model=PeriodResponse, status_code=201
)
def create_period(company_id: int, payload: PeriodCreate, db: DB):
    return {"data": service.create_period(db, company_id, payload)}


@router.get("/companies/{company_id}/periods", response_model=PeriodsResponse)
def list_periods(company_id: int, db: DB):
    service.get_company(db, company_id)
    return {
        "data": db.scalars(
            select(Period)
            .where(Period.company_id == company_id)
            .order_by(Period.year.desc(), Period.month.desc())
        ).all()
    }


@router.get("/periods/{period_id}", response_model=PeriodResponse)
def read_period(period_id: int, db: DB):
    return {"data": service.get_period(db, period_id)}
