import { useEffect, useState } from "react";
import { months } from "../types";
import type { Company, Period } from "../types";
import type { Transaction } from "../types/manual";
import { errorMessage } from "../types/manual";
import { useDre } from "../services/useDre";
import { formatMoney, formatMargin } from "../types/dre";
import { api } from "../services/api";
export function Overview({ company, period, onRevenues }: { company: Company; period: Period; onRevenues: () => void }) {
  const { data: dre, error: dreError, retry } = useDre(period.id);
  const [progress, setProgress] = useState<[number, number] | null>(null), [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([api<Transaction[]>(`/periods/${period.id}/revenues`), api<Transaction[]>(`/periods/${period.id}/expenses`)])
      .then(lists => { if (active) setProgress(lists.map(items => items.length ? Math.round(items.filter(t => t.classification_status === "CONFIRMED").length * 100 / items.length) : 0) as [number, number]); })
      .catch(err => { if (active) setError(errorMessage(err)); });
    return () => { active = false; };
  }, [period.id]);
  return <>
    <span className="eyebrow">VISÃO DO FECHAMENTO</span><h1>DRE — {months[period.month - 1]}/{period.year}</h1>
    <p>{company.name} <span className="badge">{period.status === "closed" ? "Fechado" : "Rascunho"}</span></p>
    {company.guided_mode && <p className="help">Os indicadores usam a competência dos lançamentos. O progresso abaixo indica a classificação dos registros cadastrados neste período.</p>}
    {error && <p role="alert" className="error">{error}</p>}
    {dreError && <p role="alert" className="error">{dreError}<button onClick={retry}>Tentar novamente</button></p>}
    {dre && <><div className="metrics dashboard-results">
      {[["Receita Líquida", formatMoney(dre.net_revenue, company.currency)], ["Custos", formatMoney(dre.costs, company.currency)], ["Despesas", formatMoney(dre.operating_expenses, company.currency)], ["Resultado Líquido", formatMoney(dre.net_result, company.currency)], ["Margem Líquida", formatMargin(dre.margins.net)]].map(([title, value]) => <section className="card metric" key={title}><h2>{title}</h2><strong>{value}</strong></section>)}
    </div>{dre.data_quality.has_pending_items && <p className="notice" role="status">DRE provisória: há valores pendentes que não entram nos resultados.</p>}</>}
    <div className="metrics">
      {[["Receitas", progress ? `${progress[0]}%` : "—"], ["Saídas", progress ? `${progress[1]}%` : "—"], ["Informações complementares", "Ajustes manuais"], ["Pendências", dre ? String(dre.data_quality.pending_transactions + dre.data_quality.pending_adjustments) : "—"], ["DRE", dre ? (dre.status === "PROVISIONAL" ? "Provisória" : "Calculada") : "—"]].map(([title, value]) => <section className="card metric" key={title}><h2>{title}</h2><strong>{value}</strong>{value.endsWith("%") && <div className="progress" role="progressbar" aria-label={title} aria-valuenow={parseInt(value)} aria-valuemin={0} aria-valuemax={100}><div style={{ width: value }} /></div>}</section>)}
    </div>
    <div className="next"><button className="primary" onClick={onRevenues}>Começar pelas Receitas</button></div>
  </>;
}
