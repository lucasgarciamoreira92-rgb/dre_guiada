import { months } from "../types";
import type { Company, Period } from "../types";
export function Overview({
  company,
  period,
}: {
  company: Company;
  period: Period;
}) {
  return (
    <>
      <span className="eyebrow">VISÃO DO FECHAMENTO</span>
      <h1>
        DRE — {months[period.month - 1]}/{period.year}
      </h1>
      <p>
        {company.name} <span className="badge">Rascunho</span>
      </p>
      {company.guided_mode && (
        <p className="help">
          Este é o ponto de partida da sua DRE. As próximas etapas serão
          liberadas nos próximos marcos.
        </p>
      )}
      <div className="metrics">
        {[
          ["Receitas", "0%"],
          ["Saídas", "0%"],
          ["Informações complementares", "Pendente"],
          ["Pendências", "0"],
          ["DRE", "Ainda não disponível"],
        ].map(([title, value]) => (
          <section className="card metric" key={title}>
            <h2>{title}</h2>
            <strong>{value}</strong>
            {value === "0%" && (
              <div
                className="progress"
                role="progressbar"
                aria-label={title}
                aria-valuenow={0}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            )}
          </section>
        ))}
      </div>
      <div className="next">
        <button className="primary" disabled>
          Começar pelas Receitas
        </button>
        <p className="muted">Disponível no próximo marco.</p>
      </div>
    </>
  );
}
