import { useEffect, useState } from "react";
import type { Company, Period } from "../types";
import { months } from "../types";
import type { DreDetails, DreLine, ResultLine } from "../types/dre";
import { dreLabels, formatMoney, formatMargin, guidedText } from "../types/dre";
import { errorMessage } from "../types/manual";
import { api } from "../services/api";
import { useDre } from "../services/useDre";
import { Modal } from "../components/Modal";
const lines: { key: ResultLine; sign: string; detail?: boolean; result?: boolean }[] = [
  { key: "gross_revenue", sign: "", detail: true },
  { key: "revenue_deductions", sign: "−", detail: true },
  { key: "net_revenue", sign: "=", result: true },
  { key: "costs", sign: "−", detail: true },
  { key: "gross_result", sign: "=", result: true },
  { key: "operating_expenses", sign: "−", detail: true },
  { key: "operating_result", sign: "=", result: true },
  { key: "financial_revenue", sign: "+", detail: true },
  { key: "financial_expense", sign: "−", detail: true },
  { key: "financial_result", sign: "=", result: true },
  { key: "result_before_tax", sign: "=", result: true },
  { key: "profit_taxes", sign: "−", detail: true },
  { key: "net_result", sign: "=", result: true },
];
function LineDetails({ line, company, period, onClose }: { line: DreLine; company: Company; period: Period; onClose: () => void }) {
  const [data, setData] = useState<DreDetails | null>(null), [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setData(null); setError("");
    api<DreDetails>(`/periods/${period.id}/dre/${line}/details`).then(result => { if (active) setData(result); }).catch(err => { if (active) setError(errorMessage(err)); });
    return () => { active = false; };
  }, [period.id, line, attempt]);
  return <Modal title={`Detalhamento — ${dreLabels[line]}`} onClose={onClose}>
    {error ? <p role="alert" className="error">{error}<button onClick={() => setAttempt(attempt + 1)}>Tentar novamente</button></p> : !data ? <p role="status">Carregando detalhamento…</p> : <>
      <p className="detail-total">{formatMoney(data.total, company.currency)} · {data.count} registro(s)</p>
      <ul className="detail-groups">{data.groups.map((group, index) => <li key={`${group.subcategory_id}-${index}`}><span>{group.name}<small>{group.count} registro(s)</small></span><strong>{formatMoney(group.total, company.currency)}</strong></li>)}</ul>
      {data.count === 0 && <p>Nenhum registro compõe esta linha.</p>}
      {data.items.length > 0 && <><h3>Registros de origem</h3><p className="muted">Para corrigir, abra o registro de origem.</p><ul className="detail-items">{data.items.map(item => <li key={`${item.source_type}-${item.id}`}>
        <strong>{item.description}</strong><span>{formatMoney(item.amount, company.currency)}</span>
        <small>{item.source_type === "TRANSACTION" ? "Lançamento" : "Ajuste"} #{item.id} · Competência {String(item.competence_month).padStart(2, "0")}/{item.competence_year}{item.transaction_date ? ` · Data ${item.transaction_date.split("-").reverse().join("/")}` : ""}</small>
        <a href={`/?period=${item.period_id}&area=${item.source_type === "ADJUSTMENT" ? "adjustments" : item.direction === "IN" ? "revenues" : "expenses"}#${item.source_type === "ADJUSTMENT" ? "adjustment" : "transaction"}-${item.id}`}>Abrir registro de origem</a>
      </li>)}</ul></>}
    </>}
  </Modal>;
}
export function DrePage({ company, period, onAdjustments }: { company: Company; period: Period; onAdjustments: () => void }) {
  const { data, error, retry } = useDre(period.id);
  const [selected, setSelected] = useState<DreLine | null>(null);
  return <>
    <span className="eyebrow">RESULTADOS POR COMPETÊNCIA</span><h1>DRE — {months[period.month - 1]}/{period.year}</h1>
    {error ? <p role="alert" className="error">{error}<button onClick={retry}>Tentar novamente</button></p> : !data ? <p role="status">Calculando DRE…</p> : <>
      <div className="section-heading"><p>{company.name} <span className={`status ${data.status === "PROVISIONAL" ? "pending" : ""}`}>{data.status === "PROVISIONAL" ? "Provisória" : "Calculada"}</span></p><button onClick={onAdjustments}>Informar ajustes do período</button></div>
      {data.data_quality.has_pending_items && <p role="status" className="notice">Existem {data.data_quality.pending_transactions} lançamento(s) e {data.data_quality.pending_adjustments} ajuste(s) pendentes. Esses valores não entram nesta DRE.</p>}
      <div className="dre-sheet">{lines.map(line => <section key={line.key} className={`dre-line ${line.result ? "dre-result" : ""} ${line.key === "net_result" ? "dre-final" : ""}`} data-line={line.key}>
        <div><div className="dre-label"><span aria-hidden="true">{line.sign}</span>{line.detail ? <button onClick={() => setSelected(line.key as DreLine)} aria-label={`Detalhar ${dreLabels[line.key]}`}>{dreLabels[line.key]} <small aria-hidden="true">↗</small></button> : <h2>{dreLabels[line.key]}</h2>}</div>
          {company.guided_mode && guidedText[line.key] && <p className="guide-note">{guidedText[line.key]}</p>}
        </div><strong className="dre-value">{formatMoney(data[line.key], company.currency)}</strong>
      </section>)}</div>
      <div className="metrics dre-margins">{([['gross', 'Margem Bruta'], ['operating', 'Margem Operacional'], ['net', 'Margem Líquida']] as const).map(([key, label]) => <section className="card metric" key={key} data-margin={key}><h2>{label}</h2><strong>{formatMargin(data.margins[key])}</strong>{company.guided_mode && <p className="guide-note">{guidedText[`margin_${key}`]}</p>}</section>)}</div>
      {data.margins.net === null && <p className="muted">Margens não se aplicam quando a receita líquida é zero ou negativa.</p>}
      {company.guided_mode && <p className="help">A DRE considera a competência, mesmo que a movimentação tenha ocorrido em outro mês. Clique nas linhas para ver de onde veio cada valor.</p>}
    </>}
    {selected && <LineDetails line={selected} company={company} period={period} onClose={() => setSelected(null)} />}
  </>;
}
