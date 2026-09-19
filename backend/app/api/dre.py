from fastapi import APIRouter
from app.api.routes import DB
from app.dre import service
from app.dre.schemas import (AdjustmentCreate, AdjustmentResponse, AdjustmentsResponse,
                             DetailsResponse, DreResponse, Line)

router = APIRouter()


@router.get('/periods/{period_id}/dre', response_model=DreResponse)
def dre(period_id: int, db: DB):
    result, _ = service.calculate_period(db, period_id)
    return {'data': result}


@router.get('/periods/{period_id}/dre/{line}/details', response_model=DetailsResponse)
def details(period_id: int, line: Line, db: DB):
    _, detail = service.calculate_period(db, period_id)
    return {'data': detail[line]}


@router.get('/periods/{period_id}/adjustments', response_model=AdjustmentsResponse)
def adjustments(period_id: int, db: DB):
    return {'data': service.list_adjustments(db, period_id)}


@router.post('/periods/{period_id}/adjustments', response_model=AdjustmentResponse, status_code=201)
def create_adjustment(period_id: int, payload: AdjustmentCreate, db: DB):
    return {'data': service.create_adjustment(db, period_id, payload)}
