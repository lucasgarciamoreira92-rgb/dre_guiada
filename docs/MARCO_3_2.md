# Marco 3.2 — Validação Visual Interativa

Execute no desktop do Mac oficial:

```bash
./scripts/validate_local.sh
./scripts/validate_visual.sh
```

No Mac Apple Silicon, o script prefere o Node 22 do Homebrew quando instalado,
seguindo `.nvmrc`; Node 26 apresentou travamento na finalização do trace.

O segundo comando abre Chromium headed, com ações desaceleradas e viewport
1440×900. Exige sessão gráfica ativa, Chromium instalado pelo Playwright e portas
8000/5173 livres. Não reutiliza servidores existentes. O backend usa um SQLite
temporário criado por migrations e removido ao encerrar; nenhum cadastro de teste
é enviado ao banco persistente.

O fluxo cadastra Empresa Visual DRE, Agosto/2026, Mensalidades (100.000), Link IP
(20.000 / Infraestrutura), Google Workspace (1.500 / Tecnologia) e Servidor
(30.000 / Equipamentos) pelos formulários. Passa por Boas-vindas, Empresa e
período, Visão Geral, Receitas, Saídas, Informações Complementares, Visão Geral,
DRE, drilldown com origem e Configurações. Confirma persistência após reload.

A DRE deve mostrar receita bruta/líquida 100.000, custos 20.000, resultado bruto
80.000, despesas 1.500, resultado operacional/líquido 78.500, margens 80%, 78,5%
e 78,5%. O investimento permanece cadastrado sem reduzir a DRE.

Cada execução cria `validation-results/visual/<timestamp>/` com 16 screenshots,
vídeo WebM, trace Playwright, log, resultado Playwright e `report.json`. O relatório
compara integridade SQLite, foreign keys, contagens e SHA-256 do dump lógico antes
e depois. Divergência, evidência ausente ou teste reprovado retorna código não zero.
Os artefatos são locais e ignorados pelo Git. Revise as imagens/vídeo e confirme a
janela visível no desktop; a execução automatizada não substitui essa observação.
O Playwright encerra navegador e servidores ao terminar.

Marco 4 não integra esta implementação.
