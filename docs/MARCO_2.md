# Marco 2 — Lançamentos Manuais

Implementação limitada a receitas, saídas e subcategorias. Não há motor de DRE,
importação, IA, fechamento, regras tributárias completas ou integração externa.

## Decisões de dados

- O período identifica o conjunto de lançamentos. A competência é independente
  da data e pode ser diferente do mês do período. Não ocorre transferência
  automática entre períodos.
- Valores positivos com até 12 dígitos inteiros e duas casas decimais.
  A API serializa Decimal como texto. O tipo SQLAlchemy Money usa Numeric(14,2)
  como base e BIGINT em centavos no SQLite, evitando conversão para float.
  Totais da interface usam BigInt em centavos, sem cálculo de DRE.
- Company e Period são derivados da rota: não podem ser enviados ou trocados
  por campos da requisição. Direction é imutável após a criação.
- A descrição original é preservada após editar a descrição atual.
- Origem MANUAL, competência CONFIRMED/USER. Categoria UNDEFINED gera
  classificação PENDING; as demais geram CONFIRMED. TAX mantém efeito PENDING
  e include_in_dre=false, mesmo com classificação confirmada.
- Investimentos e NON_DRE têm NO_EFFECT e include_in_dre=false.
- Subcategoria é opcional. Ao trocar categoria no formulário, a seleção é
  limpa. A API rejeita vínculo incompatível, inclusive de outra empresa.
- Nomes de subcategorias são comparados por casefold e espaços normalizados;
  a restrição inclui nomes arquivados. Podem existir nomes iguais em categorias
  ou empresas diferentes.
- Subcategorias padrão não são editáveis; podem ser arquivadas. Personalizadas
  permitem edição. Não é possível trocar a categoria de uma subcategoria usada.
  Arquivar impede novos vínculos e preserva lançamentos existentes, inclusive
  sua edição sem troca do vínculo.
- Excluir lançamento exige confirmação na interface e faz DELETE físico.
  Criar, editar ou excluir em um período com status closed é rejeitado.
  Não há operação de fechamento neste marco.

## Migration e integridade

`0002_m2_transactions_subcategories.py` cria transactions e subcategories.
A migration 0001 permanece idêntica. Índices por empresa, período/direção e
subcategoria. Chaves compostas garantem empresa/período e
empresa/categoria/subcategoria compatíveis também no banco.
Checks validam direção/categoria, valor positivo, competência, descrição,
origem, classificação e efeito. Nomes normalizados são únicos por empresa/categoria.

As 20 subcategorias padrão são inseridas pela migration para empresas existentes
e na mesma transação do cadastro de novas empresas. GET não cria dados.
A migration contém uma cópia fixa dos padrões, independente do código futuro.
Nenhum lançamento financeiro fictício é inserido no banco de desenvolvimento.

## API

| Método | Rota |
| --- | --- |
| POST | /periods/{period_id}/transactions |
| GET | /periods/{period_id}/revenues |
| GET | /periods/{period_id}/expenses |
| GET/PATCH/DELETE | /transactions/{transaction_id} |
| GET/POST | /companies/{company_id}/subcategories |
| PATCH | /subcategories/{subcategory_id} |
| POST | /subcategories/{subcategory_id}/archive |

GET subcategories admite `main_category`; inclui arquivadas para consulta do
histórico e configurações. Todas as respostas mantêm os envelopes data/error.
Erros: 404 para recurso ausente; 422 para dados/vínculos inválidos; 409 para
período fechado, nome duplicado, edição de padrão ou mudança de categoria em uso.

## Interface

Receitas e Saídas: formulário, lista, total, quantidade, busca por descrição,
filtros de classificação, edição, exclusão confirmada e ajuda pelo Modo Guiado.
O total e a quantidade representam todos os lançamentos da área; os filtros
alteram apenas a lista. Subcategoria personalizada pode ser criada no formulário
com categoria fixa e seleção imediata, ou nas configurações.

Visão do Fechamento: proporção simples de itens classificados em cada direção,
com 0% quando vazia. O percentual não representa uma DRE calculada nem prontidão
financeira definitiva. Demais áreas futuras continuam desabilitadas.

## Validação e Mac

```bash
cd /Users/lucasmoreira/Projetos/dre_guiada
git pull --ff-only
(cd backend && .venv/bin/python -m alembic upgrade head)
./scripts/validate_local.sh
```

O validador executa todos os testes backend, build e Chromium. Os testes criam
bancos temporários via migrations, incluindo upgrade de uma base 0001 com dados,
downgrade/upgrade e verificação de diferenças do schema. O E2E cria os quatro
lançamentos pedidos (Mensalidades, Link IP, Google Workspace e Servidor),
confere persistência, separação das listas, valores e NO_EFFECT do investimento.
Também cobre CRUD, filtros, criação/edição/arquivamento de subcategoria,
Modo Guiado, erros amigáveis e bloqueio de envio duplo.

A execução desta implementação ocorreu em Linux. O Mac não estava acessível:
é necessário executar o comando acima nele e conferir o relatório com plataforma
Darwin e o mesmo commit antes de considerar o Marco 2 concluído.

## Resultado nesta sessão

Validador completo em Linux: exit code 0, 88 testes backend aprovados,
7 E2E Chromium aprovados e build TypeScript/Vite aprovado. Zero testes falhando.
A migration 0001 foi comparada com o commit-base e permanece inalterada.
A verificação de migração cobriu base vazia e empresa/período existentes.
O bloqueio inicial dos E2E foi corrigido com nomes acessíveis explícitos nos
seletores. Os avisos de proxy npm e cores do terminal são ambientais.
A validação no Mac permanece pendente por falta de acesso direto nesta sessão.
