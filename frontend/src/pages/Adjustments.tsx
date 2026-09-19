import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import type { Company, Period } from "../types";
import { months } from "../types";
import type { Adjustment, AdjustmentType, DeductionKind } from "../types/dre";
import { adjustmentLabels, deductionLabels, formatMoney } from "../types/dre";
import { errorMessage } from "../types/manual";
import { api } from "../services/api";
export function Adjustments({ company, period }: { company: Company; period: Period }) {
  const [items, setItems] = useState<Adjustment[]>([]), [loading, setLoading] = useState(true);
  const [type, setType] = useState<AdjustmentType>("PROFIT_TAX"), [kind, setKind] = useState<DeductionKind>("REVENUE_TAX");
  const [amount, setAmount] = useState(""), [observation, setObservation] = useState("");
  const [error, setError] = useState(""), [busy, setBusy] = useState(false), [saved, setSaved] = useState(false);
  const lock = useRef(false);
  async function load() {
    setLoading(true); setError("");
    try { setItems(await api<Adjustment[]>(`/periods/${period.id}/adjustments`)); }
    catch (err) { setError(errorMessage(err)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [period.id]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (lock.current) return;
    setSaved(false);
    const decimal = amount.trim().replace(",", ".");
    if (!/^\d{1,12}(\.\d{1,2})?$/.test(decimal) || !/[1-9]/.test(decimal)) { setError("Informe um valor positivo com até duas casas decimais."); return; }
    if (!observation.trim()) { setError("Informe a justificativa do ajuste."); return; }
    lock.current = true; setBusy(true); setError("");
    try {
      const item = await api<Adjustment>(`/periods/${period.id}/adjustments`, "POST", { type, amount: decimal, observation, deduction_kind: type === "REVENUE_DEDUCTION" ? kind : null });
      setItems([...items, item]); setAmount(""); setObservation(""); setSaved(true);
    } catch (err) { setError(errorMessage(err)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <>
    <span className="eyebrow">INFORMAÇÕES COMPLEMENTARES</span><h1>Ajustes — {months[period.month - 1]}/{period.year}</h1>
    {company.guided_mode && <p className="help">Informe valores apurados para a competência deste período. Deduções reduzem a receita bruta; tributos sobre lucro reduzem o resultado antes dos tributos.</p>}
    <form className="card" onSubmit={submit}>
      <h2>Adicionar ajuste</h2><fieldset disabled={busy || loading || period.status === "closed"}>
        <div className="form-row"><label>Tipo de ajuste<select aria-label="Tipo de ajuste" value={type} onChange={e => setType(e.target.value as AdjustmentType)}>{(Object.keys(adjustmentLabels) as AdjustmentType[]).map(key => <option key={key} value={key}>{adjustmentLabels[key]}</option>)}</select></label>
        <label>Valor<input required inputMode="decimal" placeholder="5000,00" value={amount} onChange={e => setAmount(e.target.value)} /></label></div>
        {type === "REVENUE_DEDUCTION" && <label>Tipo de dedução<select aria-label="Tipo de dedução" value={kind} onChange={e => setKind(e.target.value as DeductionKind)}>{(Object.keys(deductionLabels) as DeductionKind[]).map(key => <option key={key} value={key}>{deductionLabels[key]}</option>)}</select></label>}
        {type === "OTHER_ADJUSTMENT" && <p className="notice">Este ajuste não tem efeito definido e ficará pendente, sem entrar na DRE.</p>}
        <label>Justificativa<textarea required maxLength={2000} value={observation} onChange={e => setObservation(e.target.value)} placeholder="Descreva a origem e a apuração do valor." /></label>
        <button className="primary">{busy ? "Salvando…" : "Salvar ajuste"}</button>
      </fieldset>
      {saved && <p role="status">Ajuste registrado.</p>}
    </form>
    {error && <p role="alert" className="error">{error}<button onClick={() => void load()}>Recarregar ajustes</button></p>}
    <h2>Ajustes registrados</h2>
    {loading ? <p role="status">Carregando ajustes…</p> : items.length === 0 ? <p>Nenhum ajuste informado.</p> : <ul className="adjustment-list">{items.map(item => <li id={`adjustment-${item.id}`} key={item.id} className="card"><div className="section-heading"><strong>{adjustmentLabels[item.type]}</strong><strong>{formatMoney(item.amount, company.currency)}</strong></div>{item.deduction_kind && <p>{deductionLabels[item.deduction_kind]}</p>}<p>{item.observation}</p><small>Ajuste #{item.id} · {item.status === "PENDING" ? "Pendente — fora da DRE" : "Confirmado"} · {new Date(item.created_at).toLocaleDateString("pt-BR")}</small></li>)}</ul>}
  </>;
}
