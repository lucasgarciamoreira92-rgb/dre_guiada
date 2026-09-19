import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api.routes import router
from app.api.manual import router as manual_router
from app.core.errors import AppError

app = FastAPI(title="DRE Guiada — Marco 2", version="0.1.0")
app.include_router(router)
app.include_router(manual_router)


def error(code, message, status, details=None):
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


@app.exception_handler(AppError)
async def app_error(request: Request, exc: AppError):
    return error(exc.code, exc.message, exc.status)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    messages = {
        "name": "Informe o nome da subcategoria." if "subcategories" in request.url.path else "Informe o nome da empresa.",
        "amount": "Informe um valor maior que zero, com até duas casas decimais e 12 dígitos inteiros.",
        "description": "Informe uma descrição válida.",
        "competence_month": "A competência deve ter mês entre 1 e 12.",
        "competence_year": "O ano da competência deve estar entre 1900 e 2100.",
        "transaction_date": "Informe uma data válida.",
        "main_category": "Escolha uma categoria válida.",
        "direction": "Escolha receita ou saída.",
        "month": "O mês deve ser um número inteiro entre 1 e 12.",
        "year": "O ano deve ser um número inteiro entre 1900 e 2100.",
        "currency": "Informe a moeda com três letras.",
        "guided_mode": "Informe se o Modo Guiado está ativo.",
    }
    fields = [
        {
            "field": str(e["loc"][-1]),
            "message": messages.get(
                str(e["loc"][-1]), "Verifique o valor informado neste campo."
            ),
        }
        for e in exc.errors()
    ]
    return error("VALIDATION_ERROR", fields[0]["message"], 422, {"fields": fields})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return error(
        "HTTP_ERROR",
        "Recurso não encontrado."
        if exc.status_code == 404
        else "Solicitação não permitida.",
        exc.status_code,
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Erro inesperado na API")
    return error("INTERNAL_ERROR", "Não foi possível concluir. Tente novamente.", 500)
