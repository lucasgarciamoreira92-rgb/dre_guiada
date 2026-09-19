from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from app.schemas.entities import Input, Name

Category = Literal['REVENUE_RECURRING','REVENUE_SERVICE','REVENUE_PRODUCT','REVENUE_OTHER_OPERATING','FINANCIAL_REVENUE','NON_DRE','UNDEFINED','COST','EXPENSE','INVESTMENT','FINANCIAL_EXPENSE','TAX']
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Amount = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2, allow_inf_nan=False)]
Month = Annotated[int, Field(ge=1, le=12, strict=True)]
Year = Annotated[int, Field(ge=1900, le=2100, strict=True)]


class TransactionCreate(Input):
    direction: Literal['IN', 'OUT']
    transaction_date: date
    competence_month: Month
    competence_year: Year
    description: Description
    amount: Amount
    main_category: Category
    subcategory_id: int | None = Field(default=None, gt=0)
    observation: str | None = Field(default=None, max_length=2000)


class TransactionPatch(Input):
    transaction_date: date | None = None
    competence_month: Month | None = None
    competence_year: Year | None = None
    description: Description | None = None
    amount: Amount | None = None
    main_category: Category | None = None
    subcategory_id: int | None = Field(default=None, gt=0)
    observation: str | None = Field(default=None, max_length=2000)

    @model_validator(mode='after')
    def non_nullable(self):
        for key in self.model_fields_set - {'subcategory_id', 'observation'}:
            if getattr(self, key) is None:
                raise ValueError('Campo obrigatório não pode ser nulo.')
        return self


class TransactionRead(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    period_id: int
    original_description: str
    competence_status: str
    competence_source: str
    dre_effect: str
    classification_status: str
    include_in_dre: bool
    origin_type: str
    created_at: datetime
    updated_at: datetime


class SubcategoryCreate(Input):
    main_category: Category
    name: Name
    description: str | None = Field(default=None, max_length=1000)


class SubcategoryPatch(Input):
    main_category: Category | None = None
    name: Name | None = None
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode='after')
    def non_nullable(self):
        for key in self.model_fields_set - {'description'}:
            if getattr(self, key) is None:
                raise ValueError('Campo obrigatório não pode ser nulo.')
        return self


class SubcategoryRead(SubcategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class TransactionResponse(BaseModel):
    data: TransactionRead


class TransactionsResponse(BaseModel):
    data: list[TransactionRead]


class SubcategoryResponse(BaseModel):
    data: SubcategoryRead


class SubcategoriesResponse(BaseModel):
    data: list[SubcategoryRead]
