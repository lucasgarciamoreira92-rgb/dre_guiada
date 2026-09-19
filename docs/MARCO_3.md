# Marco 3 — Motor da DRE

Motor determinístico, exclusivamente no backend. Módulos em `app/dre/`:
`calculator.py` (cálculo puro), `rules.py` (mapas e arredondamento),
`schemas.py` (entradas e respostas), `validator.py` (elegibilidade) e
`service.py` (leitura do banco). Nenhum resultado é recebido do frontend.

## Competência e origem

O filtro da DRE é empresa + competence_month + competence_year, com índice
específico. O período de cadastro e transaction_date não determinam a inclusão.
Assim, uma receita cadastrada no período de setembro, movimentada em 05/09/2026,
com competência agosto aparece somente na DRE de agosto da mesma empresa.
As listas de Receitas/Saídas continuam mostrando o período de cadastro,
conforme o Marco 2. O detalhamento informa o período de origem e oferece link
para localizar esse lançamento, inclusive quando pertence a outro período.

O motor não altera status do período, não fecha/reabre e não persiste resultados.
Cada consulta recalcula a partir dos dados atuais. Os status CALCULATED e
PROVISIONAL são próprios da resposta DRE; não substituem draft etc. no Period.

## Fórmulas

- Receita Bruta: soma de GROSS_REVENUE.
- Deduções: soma dos ajustes REVENUE_DEDUCTION explicitamente informados.
- Receita Líquida = Receita Bruta − Deduções.
- Custos: soma de COST.
- Resultado Bruto = Receita Líquida − Custos.
- Despesas Operacionais: soma de OPERATING_EXPENSE.
- Resultado Operacional = Resultado Bruto − Despesas Operacionais.
- Resultado Financeiro = FINANCIAL_REVENUE − FINANCIAL_EXPENSE.
- Resultado Antes dos Tributos = Resultado Operacional + Resultado Financeiro.
- Tributos sobre Lucro: soma dos ajustes PROFIT_TAX confirmados.
- Resultado Líquido = Resultado Antes dos Tributos − Tributos sobre Lucro.
- Margens bruta, operacional e líquida: resultado correspondente / receita
  líquida × 100, somente se receita líquida > 0; caso contrário, null.

Decimal com contexto de 40 dígitos; exibição com duas casas e ROUND_HALF_UP.
A API mantém valores decimais como strings, seguindo o padrão do Marco 2,
para preservar centavos. O frontend somente formata os resultados recebidos,
inclusive valores negativos e percentuais; não calcula linhas ou margens.

## Ajustes explícitos e rastreabilidade

A nova tabela period_adjustments mantém id, period_id, type, amount, status,
observation, created_at e updated_at. Acrescenta dre_effect e deduction_kind
para representar deduções sem alterar o mapa de categorias do Marco 2.

| Tipo | Efeito | Status |
| --- | --- | --- |
| PROFIT_TAX | PROFIT_TAX, na linha profit_taxes | CONFIRMED |
| REVENUE_DEDUCTION | REVENUE_DEDUCTION | CONFIRMED |
| OTHER_ADJUSTMENT | PENDING, sem contribuição | PENDING |

REVENUE_DEDUCTION exige exatamente um subtipo: REVENUE_TAX (imposto sobre
receita), RETURN (devolução), DISCOUNT (abatimento) ou OTHER_APPROVED (outra
dedução aprovada). Essa é a via complementar controlada adotada neste marco.
A observação/justificativa é obrigatória em todos os ajustes, e o valor é
positivo com duas casas. Status e efeito são derivados no backend.

A competência do ajuste é a do período ao qual ele pertence. Não existe
inferência sobre um Transaction TAX: ele permanece PENDING e não entra no
cálculo. Um ajuste de tributo informado separadamente não classifica nem altera
esse lançamento. OTHER_ADJUSTMENT também não é aplicado implicitamente.
Não há regra tributária, aprovação avançada ou módulo de ajustes sofisticado.
A API e a interface implementam apenas cadastro e consulta de ajustes.

Detalhes de linha usam o mesmo cálculo e seleção da DRE. Retornam total,
quantidade, grupos e registros resumidos com origem TRANSACTION ou ADJUSTMENT,
id, valor, descrição/justificativa, competência e período de origem.
Subcategorias arquivadas continuam identificáveis no histórico.

## Pendências e exclusões

INVESTMENT e NON_DRE não contribuem para nenhuma linha, inclusive NON_DRE IN.
UNDEFINED, PENDING e inconsistências de classificação são excluídos e contados
em pending_transactions. Ajustes sem regra são contados em pending_adjustments.
Se houver pendências, status PROVISIONAL e has_pending_items=true; caso
contrário, CALCULATED. Uma DRE vazia tem valores zero e margens null.
Não foi criada Central de Pendências nem readiness definitiva.

## API

| Método | Endpoint |
| --- | --- |
| GET | /periods/{period_id}/dre |
| GET | /periods/{period_id}/dre/{line}/details |
| GET | /periods/{period_id}/adjustments |
| POST | /periods/{period_id}/adjustments |

Linhas detalháveis: gross_revenue, revenue_deductions, costs,
operating_expenses, financial_revenue, financial_expense e profit_taxes.
POST adjustments aceita type, amount, observation e deduction_kind opcional.
Período inexistente: 404. Dados ou linha inválidos: 422. Criação de ajuste em
período fechado: 409. Envelopes data/error preservados.

## Migration

`0003_m3_dre_engine_adjustments.py`: cria period_adjustments e índice de
competência em transactions. Foreign key para periods e constraints de tipo,
valor positivo, justificativa e combinações de tipo/status/efeito/subtipo.
Valores usam o mesmo tipo monetário exato do Marco 2: centavos inteiros no SQLite.
As migrations 0001 e 0002 permanecem imutáveis.

## Frontend

DRE ativa com resultados destacados, três margens, mensagens curtas do Modo
Guiado e painel de detalhes somente para leitura. Links levam à origem.
Dashboard exibe receita líquida, custos, despesas operacionais, resultado líquido
e margem líquida vindos da API. Informações Complementares permite informar
somente os ajustes mínimos descritos acima. Não há gráficos novos.

## Cenários validados

| Resultado | Cenário 1 | Cenário 2 |
| --- | ---: | ---: |
| Receita Bruta | 100.000,00 | 100.000,00 |
| Deduções | 0,00 | 10.000,00 |
| Receita Líquida | 100.000,00 | 90.000,00 |
| Custos | 20.000,00 | 30.000,00 |
| Resultado Bruto | 80.000,00 | 60.000,00 |
| Despesas Operacionais | 1.500,00 | 20.000,00 |
| Resultado Operacional | 78.500,00 | 40.000,00 |
| Receita Financeira | 0,00 | 2.000,00 |
| Despesa Financeira | 0,00 | 1.000,00 |
| Resultado Financeiro | 0,00 | 1.000,00 |
| Resultado Antes dos Tributos | 78.500,00 | 41.000,00 |
| Tributos sobre Lucro | 0,00 | 5.000,00 |
| Resultado Líquido | 78.500,00 | 36.000,00 |
| Margem Bruta | 80,00% | 66,67% |
| Margem Operacional | 78,50% | 44,44% |
| Margem Líquida | 78,50% | 40,00% |

## Validação nesta sessão

Linux: `./scripts/validate_local.sh` aprovado, exit code 0. 128 testes backend
(incluindo suíte financeira, API, migrations e regressões) e 11 E2E aprovados.
Build TypeScript/Vite aprovado. Interface revisada em desktop e 390 px.
E2E confirmou os quatro registros obrigatórios, investimento excluído, detalhes,
Modo Guiado, ajustes explícitos, DRE provisória, negativos e competência entre
períodos. Testes usam bancos temporários; não há seed financeiro na base local.
As migrations foram testadas do zero e sobre base 0002 com lançamento existente,
com preservação dos dados e downgrade/upgrade.

## Validação pendente no Mac

O Mac não esteve acessível nesta sessão. Executar no checkout oficial, com as
portas 8000 e 5173 livres:

```bash
cd /Users/lucasmoreira/Projetos/dre_guiada
git pull --ff-only
(cd backend && .venv/bin/python -m alembic upgrade head)
./scripts/validate_local.sh
```

O hook post-merge já executa testes ao receber mudanças; o comando explícito
acima também valida quando não há merge. Conferir o relatório mais recente em
validation-results/: plataforma Darwin, mesmo commit remoto, status passed.
Até essa confirmação, o Marco 3 é PARCIAL. Marco 4 não iniciado.
