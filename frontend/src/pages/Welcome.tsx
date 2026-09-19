export function Welcome({ onStart }: { onStart: () => void }) {
  return (
    <main className="welcome">
      <span className="eyebrow">DRE GUIADA · SEU PRIMEIRO PASSO</span>
      <h1>
        Monte sua DRE
        <br />
        de forma simples
      </h1>
      <p className="intro">
        Você não precisa dominar finanças para começar. Vamos organizar os dados
        da sua empresa passo a passo até chegar à sua DRE.
      </p>
      <ol className="steps">
        {[
          "Adicione suas receitas",
          "Adicione suas saídas",
          "Resolva as pendências",
          "Veja sua DRE",
        ].map((text, i) => (
          <li key={text}>
            <span>{i + 1}</span>
            {text}
          </li>
        ))}
      </ol>
      <button className="primary" onClick={onStart}>
        Começar minha DRE <span aria-hidden="true">→</span>
      </button>
      <p className="muted">Um passo de cada vez. Com clareza em cada etapa.</p>
    </main>
  );
}
