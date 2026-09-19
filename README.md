# DRE Guiada — MVP v0.1

Estágio atual: **Marco 1 — Fundação**. Fluxo: boas-vindas → cadastro de empresa → período mensal → visão do fechamento. Não há lançamentos, importações, IA, cálculo da DRE ou fechamento/reabertura.

## Stack e requisitos

Python 3.12+ (validado com 3.12), FastAPI, Pydantic, SQLAlchemy 2, Alembic e SQLite. React 19, TypeScript e Vite 7. Node.js 22.12+ ou 24 e npm. Chromium/Playwright somente para testes de navegador. Dependências Python fixadas em `requirements.txt`; frontend reproduzível com `package-lock.json` e `npm ci`.

## Instalação

A partir de `~/Projetos/dre_guiada`:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
cd ../frontend
npm ci
```

## Rodar localmente

Terminal do backend:

```bash
cd ~/Projetos/dre_guiada/backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal do frontend:

```bash
cd ~/Projetos/dre_guiada/frontend
npm run dev
```

Abra http://127.0.0.1:5173. Documentação da API: http://127.0.0.1:8000/docs.
O Vite encaminha `/api` ao backend, sem necessidade de CORS. Serviços restritos ao computador local. O build estático requer um servidor que encaminhe `/api` para a API; hospedagem não integra este marco.

## Banco e migrations

```bash
cd backend
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic current
.venv/bin/python -m alembic check
```

O caminho padrão do SQLite é `backend/dre_guiada.db`, independente do diretório de execução. Pode ser alterado pela variável de ambiente `DATABASE_URL` (exportada no shell; não há carregamento automático de `.env`). O banco só é criado por migrations. Não há seeds obrigatórios.

Migration `0001`: `companies` e `periods`, relacionamento 1:N, foreign key ativa em cada conexão e índice em `periods.company_id`. Constraint única `(company_id, month, year)` impede duplicidades inclusive com requisições concorrentes. Checks validam nome não vazio, mês 1–12, ano 1900–2100, progresso 0–100 e status previstos. Anos de 1900 a 2100 são a regra adotada para este marco. CNPJ opcional aceita até 18 caracteres, sem validação fiscal de dígitos verificadores. Moeda é normalizada para três letras maiúsculas, padrão BRL. Modo Guiado padrão ON. Períodos iniciam em `draft`, progresso 0, sem datas de fechamento/reabertura.

## API

| Método | Endpoint | Função |
|---|---|---|
| POST | /companies | Criar empresa |
| GET | /companies | Listar empresas |
| GET | /companies/{company_id} | Consultar empresa |
| PATCH | /companies/{company_id} | Editar empresa |
| POST | /companies/{company_id}/periods | Criar período |
| GET | /companies/{company_id}/periods | Listar períodos da empresa |
| GET | /periods/{period_id} | Consultar período |

Sucesso: `{"data": ...}`. Erros: `{"error":{"code":"...","message":"...","details":{}}}`. HTTP 201 ao criar, 200 ao consultar/editar, 422 para validação, 404 para entidade inexistente e 409 para período duplicado (`PERIOD_ALREADY_EXISTS`). Exceções internas são registradas no servidor e não expostas na interface.

## Interface

Boas-vindas com passos explicativos; formulário de empresa/período com bloqueio de envio duplicado; visão do fechamento com indicadores iniciais; menu lateral com áreas futuras desabilitadas; configurações com dados básicos e alternância persistida do Modo Guiado. Layout off-white e verde com responsividade básica.

A URL `?period=ID` permite reabrir o período persistido ao recarregar. A criação de empresa e período usa duas requisições, conforme o fluxo solicitado. Se a segunda falhar, a empresa permanece cadastrada e a tentativa seguinte reutiliza seu ID enquanto o formulário estiver aberto. Não existe transação distribuída entre essas duas chamadas. Áreas futuras são apenas marcadores visuais.

## Testes

Backend (cada caso usa SQLite temporário criado via Alembic):

```bash
cd backend
.venv/bin/python -m pytest -q
```

Build e testes reais de navegador:

```bash
cd frontend
npm run build
npx playwright install chromium
npm run test:e2e
```

Em Linux mínimo, pode ser necessário `npx playwright install --with-deps chromium` para instalar bibliotecas do navegador. Os testes E2E iniciam backend e frontend automaticamente; as portas 8000/5173 devem estar livres. Usam banco temporário isolado, nunca o banco de desenvolvimento. Cobrem Agosto/2026, persistência após reload, Modo Guiado, responsividade, falha na criação do período, repetição segura e erros amigáveis. Capturas em `frontend/test-results/`, ignoradas pelo Git.

## Estrutura

```text
dre_guiada/
  backend/
    app/
      main.py
      api/routes.py
      core/{config,errors}.py
      db/session.py
      models/entities.py
      schemas/entities.py
      services/entities.py
    alembic/versions/0001_foundation.py
    alembic/env.py
    alembic.ini
    tests/
    pytest.ini
    requirements.txt
  frontend/
    src/{pages,components,services,types,styles}/
    src/main.tsx
    tests/flow.spec.ts
    playwright.config.ts
    vite.config.ts
    tsconfig.json
    package.json
    package-lock.json
  scripts/e2e_backend.py
  README.md
  .gitignore
```

O Git ignora bancos locais, ambientes virtuais, node_modules, builds, caches e secrets. Marco 2 não implementado.
