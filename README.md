# DRE Guiada — MVP v0.1

Estágio atual: **Marco 3 — Motor da DRE**, implementado e sujeito à validação no Mac. Fluxo: empresa → período → lançamentos manuais → ajustes explícitos → DRE por competência. Não há importações, IA, fechamento/reabertura, integrações ou EBITDA. Veja [regras e validação do Marco 3](docs/MARCO_3.md).

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

Boas-vindas com passos explicativos; formulário de empresa/período com bloqueio de envio duplicado; visão do fechamento com indicadores iniciais; Receitas e Saídas com CRUD manual e menu lateral com demais áreas futuras desabilitadas; configurações com dados básicos e alternância persistida do Modo Guiado. Layout off-white e verde com responsividade básica.

A URL `?period=ID` permite reabrir o período persistido ao recarregar. A criação de empresa e período usa duas requisições, conforme o fluxo solicitado. Se a segunda falhar, a empresa permanece cadastrada e a tentativa seguinte reutiliza seu ID enquanto o formulário estiver aberto. Não existe transação distribuída entre essas duas chamadas. Áreas posteriores ao Marco 3 são apenas marcadores visuais.

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

O Git ignora bancos locais, ambientes virtuais, node_modules, builds, caches e secrets. Marco 4 não implementado.

## Padronização — Marco 1.1

Diretório oficial no Mac: `/Users/lucasmoreira/Projetos/dre_guiada`.
Execute `bash scripts/setup.sh` e `backend/.venv/bin/python scripts/validate.py`.
Veja [procedimento e limitações](docs/MARCO_1_1.md).

## Lançamentos manuais

A migration `0002_m2_transactions_subcategories.py` adiciona lançamentos e as 20 subcategorias padrão por empresa. Receitas e Saídas possuem CRUD, busca, filtros e totais exatos. Configurações permite gerenciar subcategorias. Execute `./scripts/validate_local.sh` para validar todos os marcos. Detalhes e comandos do Mac em [Marco 2](docs/MARCO_2.md).

## Motor da DRE — Marco 3

A migration `0003_m3_dre_engine_adjustments.py` adiciona ajustes do período e índice de competência. A API calcula a DRE exclusivamente no backend, com Decimal, detalhes rastreáveis e margens. O filtro é empresa + competência, independente da data ou do período de cadastro. As migrations anteriores são preservadas. Tela DRE, indicadores e ajustes explícitos estão disponíveis. Execute `./scripts/validate_local.sh` para validar todos os marcos. Fórmulas, regras de deduções e cenários em [Marco 3](docs/MARCO_3.md).

### Marco 3.1 — validação local e evidência visual

`./scripts/validate_local.sh` verifica o ambiente e o banco persistente da aplicação
(`backend/dre_guiada.db` por padrão; respeita `DATABASE_URL`, resolvida a partir de
`backend/`). Aplica `alembic upgrade head`, compara a revisão atual ao head,
verifica as seis tabelas obrigatórias e compara o schema com os modelos.
Depois executa migrations em bancos temporários e testes backend, build e E2E.
Qualquer etapa obrigatória que falhar retorna exit code diferente de zero.

O validador não apaga nem recria bancos. Se o banco estiver ausente, prepare-o
explicitamente com `cd backend && .venv/bin/alembic upgrade head`. Se houver
inconsistência, faça backup e investigue o schema/histórico antes de corrigir;
não use `alembic stamp head` para ocultar uma migration ausente.

Os E2E capturam oito telas: Boas-vindas, Empresa e período, Visão Geral,
Receitas, Saídas, Informações Complementares, DRE e Configurações. As imagens
ficam em `validation-results/screenshots/<execução>/01-welcome.png` até
`08-settings.png`, com viewport desktop de 1440×900 e captura da página completa.
Cada execução usa uma pasta nova para impedir aprovação com evidências antigas.
E2E executado isoladamente usa `validation-results/screenshots/manual/`.
Essas imagens e os relatórios são ignorados pelo Git. O JSON em
`validation-results/` registra plataforma, commit, banco, revisões, tabelas,
resultado das etapas e caminhos/quantidade dos screenshots.
