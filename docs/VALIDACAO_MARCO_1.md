# Marco 1 — Resultado da validação

Status: concluído e validado no ambiente Linux desta sessão. Projeto em `/root/Projetos/dre_guiada` (equivalente a `~/Projetos/dre_guiada` neste ambiente). Não houve acesso ao Mac do usuário; instalação e execução nesse equipamento não foram realizadas.

## Implementação

- Backend FastAPI, SQLAlchemy, Pydantic e SQLite com separação API/modelos/schemas/services/core/db.
- Company e Period com relacionamento 1:N e os campos solicitados.
- Alembic 0001 cria as tabelas do zero e oferece downgrade. Constraint única empresa/mês/ano, foreign key, índice por empresa e checks de integridade.
- Sete endpoints solicitados, envelopes de sucesso/erro, mensagens em português e validações.
- React/TypeScript/Vite: boas-vindas, empresa/período, visão do fechamento e configurações básicas.
- Modo Guiado persistido, menu com áreas futuras desabilitadas, estilo off-white/verde e responsividade básica.
- Proteção contra duplo envio; repetição da criação do período sem recriar a empresa após falha da segunda chamada.
- README, dependências fixadas, Git e .gitignore.

## Resultados finais executados

| Verificação | Resultado |
|---|---|
| Backend pytest | 36 aprovados, 0 falhando; 0,78 s |
| Playwright/Chromium | 3 aprovados, 0 falhando; 5,3 s |
| Total | 39 executados e aprovados, 0 falhando |
| TypeScript + Vite build | Compilação concluída |
| Alembic upgrade head | 0001 aplicada |
| Alembic check | Sem diferenças de schema |
| Migração do zero, downgrade e upgrade | Aprovados na suíte |
| Ruff: erros/imports | Sem ocorrências após correções |
| pip check | Sem dependências incompatíveis |
| Banco de desenvolvimento | 0 empresas, 0 períodos |

Os testes de API usam bancos SQLite temporários migrados. O E2E inicia backend e frontend reais em portas locais e usa outro banco temporário. Os servidores de testes são encerrados ao concluir. Capturas desktop (1280 px) e mobile (390 px) foram produzidas; a ausência de transbordamento horizontal em 390 px foi testada. Nenhum erro JavaScript foi capturado no fluxo principal.

## Fluxo validado

Boas-vindas → Começar minha DRE → Empresa Teste DRE / Serviços → Agosto/2026 → Continuar → DRE — Agosto/2026. Verificados na tela: Receitas 0%, Saídas 0%, Informações complementares Pendente, Pendências 0 e DRE Ainda não disponível. A API confirmou company_id, mês, ano, status draft e progresso 0. Atualizar a página preservou o período; Modo Guiado OFF/ON persistiu após reload. Botão Receitas permaneceu desabilitado.

## Problemas encontrados e corrigidos

1. Deprecações entre versões iniciais do cliente de testes, Starlette e AnyIO: versões compatíveis fixadas e dependências transitórias conferidas.
2. Aviso do Alembic por falta de path_separator: configuração atualizada.
3. Download inicial do Chromium indisponível: navegador instalado por distribuição alternativa do Playwright.
4. Testes não encontravam o nome exato do seletor de mês: rótulo acessível explícito corrigido, três testes repetidos e aprovados.
5. Ordenação dos imports e formatação revisadas. Import de registro dos modelos no Alembic preservado explicitamente.

O ambiente emite avisos de npm sobre configuração de proxy e de cores NO_COLOR/FORCE_COLOR. São avisos do executor, sem falha no build ou nos testes.

## Git e limites

Branch main; commit `feat: implement foundation for DRE Guiada MVP`. Hash verificável com `git log -1 --format=%H`. O pacote inclui o repositório Git local. Nenhum remote foi configurado e nenhum push foi realizado. Bancos, secrets, node_modules, ambientes virtuais, caches e builds não são versionados.

Sem pendências funcionais do Marco 1 no ambiente validado. A transferência/execução no Mac permanece não realizada por ausência de acesso a ele. Não houve desenvolvimento do Marco 2.
