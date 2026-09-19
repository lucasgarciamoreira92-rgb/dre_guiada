# Marco 1.1 — Git, Mac e validação

Diretório oficial no Mac: `/Users/lucasmoreira/Projetos/dre_guiada`.
O checkout Linux é apenas auxiliar; não substitui esse diretório.
Commit-base preservado: `a3e6148b767110b446d77ae93466833acee83254`.

## Preparação no Mac

Inspecione a pasta e `git status`, histórico e remotes antes de copiar ou clonar.
Nunca extraia o pacote sobre arquivos existentes sem compará-los. Não copie ambientes
virtuais ou node_modules do Linux. Use Python 3.12 e Node 22.12+ ou 24.
Na raiz do checkout, `bash scripts/setup.sh` instala as dependências fixadas,
Chromium, aplica migrations e ativa hooks locais. Preserva hooks preexistentes:
em caso de conflito, interrompe a ativação para revisão.

`backend/.venv/bin/python scripts/validate.py` executa os testes backend
(incluindo migrations do zero e reversão), build TypeScript/Vite e E2E Chromium.
As portas 8000 e 5173 precisam estar livres. Bancos de teste são temporários.
Relatórios com plataforma real, arquitetura, commit, árvore modificada e códigos
de saída ficam em `validation-results/` (ignorados pelo Git).

## Cada marco

1. Implementar apenas o marco autorizado e validar.
2. Criar commit descritivo; preservar o histórico anterior.
3. Fazer push do HEAD: o hook exige árvore limpa e repete a validação antes do envio.
4. No Mac, receber atualizações com `git pull --ff-only`: post-merge executa a validação.
5. Se dependências mudaram, repetir setup e validação. Falha no post-merge não desfaz o pull.
6. Registrar o resultado do Mac para o mesmo hash antes de declarar o marco validado nele.

Hooks são locais e devem ser instalados em cada clone. Não são controles de servidor.
Não fazem polling, não iniciam com o macOS e não recebem commits sozinhos.
Um pull sem alterações ou com rebase não dispara post-merge: execute a validação
explicitamente nesses casos. O Mac deve estar ligado e executar o fluxo acima.

## Situação observada nesta sessão

Base original: main, único commit esperado, árvore limpa, sem remotes.
Conta GitHub conectada: lucasgarciamoreira92-rgb. Consulta ao repositório
`lucasgarciamoreira92-rgb/dre_guiada` retornou 404 (inexistente ou sem acesso).
GitHub CLI ausente; conector disponível não oferece criação de repositório.
Nenhum remote inventado, nenhum push realizado. Sem acesso ao Mac nesta sessão.
Criação/configuração do remoto, publicação da base, instalação e execução no Mac
permanecem pendentes. Não confundir aprovação no Linux com aprovação no Mac.

Marco 2 não iniciado. Nenhuma alteração nas entidades, API ou funcionalidades.

## Validação da preparação

Linux: 36 testes backend e 3 testes Chromium aprovados; build aprovado.
Sintaxe dos scripts e diff verificados. Instalador de hooks verificado em repositório
temporário: configuração preexistente preservada e instalação normal aprovada.
Avisos ambientais de proxy npm e cores do terminal não impediram a execução.
