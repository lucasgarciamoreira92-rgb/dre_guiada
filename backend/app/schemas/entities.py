from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Currency = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{3}$"),
]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CompanyCreate(Input):
    name: Name
    cnpj: str | None = Field(default=None, max_length=18)
    segment: str | None = Field(default=None, max_length=120)
    currency: Currency = "BRL"
    guided_mode: bool = True


class CompanyPatch(Input):
    name: Name | None = None
    cnpj: str | None = Field(default=None, max_length=18)
    segment: str | None = Field(default=None, max_length=120)
    currency: Currency | None = None
    guided_mode: bool | None = None

    @model_validator(mode="after")
    def non_nullable(self):
        for key in ("name", "currency", "guided_mode"):
            if key in self.model_fields_set and getattr(self, key) is None:
                raise ValueError("Campo obrigatório não pode ser nulo.")
        return self


class CompanyRead(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class PeriodCreate(Input):
    month: int = Field(ge=1, le=12, strict=True)
    year: int = Field(ge=1900, le=2100, strict=True)


class PeriodRead(PeriodCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    status: Literal["draft", "provisional", "ready", "closed", "reopened"]
    completion_percentage: int
    created_at: datetime
    closed_at: datetime | None
    reopened_at: datetime | None


class CompanyResponse(BaseModel):
    data: CompanyRead


class CompaniesResponse(BaseModel):
    data: list[CompanyRead]


class PeriodResponse(BaseModel):
    data: PeriodRead


class PeriodsResponse(BaseModel):
    data: list[PeriodRead]
