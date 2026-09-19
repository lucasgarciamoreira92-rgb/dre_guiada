from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator
from app.schemas.entities import Input
from app.schemas.manual import Amount

Line = Literal['gross_revenue', 'revenue_deductions', 'costs', 'operating_expenses',
               'financial_revenue', 'financial_expense', 'profit_taxes']
AdjustmentType = Literal['PROFIT_TAX', 'OTHER_ADJUSTMENT', 'REVENUE_DEDUCTION']
DeductionKind = Literal['REVENUE_TAX', 'RETURN', 'DISCOUNT', 'OTHER_APPROVED']


@dataclass(frozen=True)
class PeriodInput:
    id: int
    company_id: int
    month: int
    year: int
    status: str = 'draft'


@dataclass(frozen=True)
class TransactionInput:
    id: int
    company_id: int
    period_id: int
    direction: str
    main_category: str
    dre_effect: str
    include_in_dre: bool
    classification_status: str
    competence_status: str
    competence_month: int
    competence_year: int
    transaction_date: date
    description: str
    amount: Decimal
    subcategory_id: int | None = None
    subcategory_name: str | None = None


@dataclass(frozen=True)
class AdjustmentInput:
    id: int
    period_id: int
    type: str
    amount: Decimal
    status: str
    observation: str
    dre_effect: str
    deduction_kind: str | None = None


class AdjustmentCreate(Input):
    type: AdjustmentType
    amount: Amount
    observation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    deduction_kind: DeductionKind | None = None

    @model_validator(mode='after')
    def explicit_deduction(self):
        if (self.type == 'REVENUE_DEDUCTION') != (self.deduction_kind is not None):
            raise ValueError('Informe um subtipo somente para deduções da receita.')
        return self


class AdjustmentRead(AdjustmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    period_id: int
    status: str
    dre_effect: str
    created_at: datetime
    updated_at: datetime


class AdjustmentResponse(BaseModel):
    data: AdjustmentRead


class AdjustmentsResponse(BaseModel):
    data: list[AdjustmentRead]


class PeriodRead(BaseModel):
    id: int
    company_id: int
    month: int
    year: int
    status: str


class Margins(BaseModel):
    gross: Decimal | None
    operating: Decimal | None
    net: Decimal | None


class DataQuality(BaseModel):
    pending_transactions: int
    pending_adjustments: int
    has_pending_items: bool


class DreRead(BaseModel):
    period: PeriodRead
    status: Literal['PROVISIONAL', 'CALCULATED']
    gross_revenue: Decimal
    revenue_deductions: Decimal
    net_revenue: Decimal
    costs: Decimal
    gross_result: Decimal
    operating_expenses: Decimal
    operating_result: Decimal
    financial_revenue: Decimal
    financial_expense: Decimal
    financial_result: Decimal
    result_before_tax: Decimal
    profit_taxes: Decimal
    net_result: Decimal
    margins: Margins
    data_quality: DataQuality


class DreResponse(BaseModel):
    data: DreRead


class DetailItem(BaseModel):
    source_type: Literal['TRANSACTION', 'ADJUSTMENT']
    id: int
    period_id: int
    direction: str | None = None
    description: str
    amount: Decimal
    transaction_date: date | None = None
    competence_month: int
    competence_year: int


class DetailGroup(BaseModel):
    subcategory_id: int | None
    name: str
    total: Decimal
    count: int


class DetailsRead(BaseModel):
    line: Line
    total: Decimal
    count: int
    transaction_count: int
    adjustment_count: int
    groups: list[DetailGroup]
    items: list[DetailItem]


class DetailsResponse(BaseModel):
    data: DetailsRead
