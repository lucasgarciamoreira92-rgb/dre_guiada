import { useEffect, useState } from "react";
import { months } from "../types";
import type { Company, Period } from "../types";
import type { Transaction } from "../types/manual";
import { errorMessage } from "../types/manual";
import { api } from "../services/api";
export function Overview({ company, period, onRevenues }: { company: Company; period: Period; onRevenues: () => void }) {
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
    {company.guided_mode && <p className="help">Adicione receitas e saídas. O progresso indica a proporção de lançamentos classificados; a DRE ainda não está disponível.</p>}
    {error && <p role="alert" className="error">{error}</p>}
    <div className="metrics">
      {[["Receitas", progress ? `${progress[0]}%` : "—"], ["Saídas", progress ? `${progress[1]}%` : "—"], ["Informações complementares", "Pendente"], ["Pendências", "0"], ["DRE", "Ainda não disponível"]].map(([title, value]) => <section className="card metric" key={title}><h2>{title}</h2><strong>{value}</strong>{value.endsWith("%") && <div className="progress" role="progressbar" aria-label={title} aria-valuenow={parseInt(value)} aria-valuemin={0} aria-valuemax={100}><div style={{ width: value }} /></div>}</section>)}
    </div>
    <div className="next"><button className="primary" onClick={onRevenues}>Começar pelas Receitas</button></div>
  </>;
}
