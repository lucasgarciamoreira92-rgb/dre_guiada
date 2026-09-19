import { useRef, useState } from "react";
import type { FormEvent } from "react";
import type { Company, Period } from "../types";
import { api } from "../services/api";
import { categoryLabels, categoryHelp, directionCategories, errorMessage } from "../types/manual";
import type { Category, Direction, Subcategory, Transaction } from "../types/manual";
import { Modal } from "./Modal";
import { SubcategoryEditor } from "./SubcategoryEditor";
export function TransactionEditor({ company, period, direction, item, subcategories, onSubcategory, onSaved, onClose }: {
  company: Company; period: Period; direction: Direction; item?: Transaction; subcategories: Subcategory[];
  onSubcategory: (sub: Subcategory) => void; onSaved: (item: Transaction) => void; onClose: () => void;
}) {
  const periodMonth = `${period.year}-${String(period.month).padStart(2, "0")}`;
  const [date, setDate] = useState(item?.transaction_date ?? `${periodMonth}-01`);
  const [competence, setCompetence] = useState(item ? `${item.competence_year}-${String(item.competence_month).padStart(2, "0")}` : periodMonth);
  const [description, setDescription] = useState(item?.description ?? "");
  const [amount, setAmount] = useState(item?.amount.replace(".", ",") ?? "");
  const [category, setCategory] = useState<Category>(item?.main_category ?? "UNDEFINED");
  const [subcategory, setSubcategory] = useState(item?.subcategory_id?.toString() ?? "");
  const [observation, setObservation] = useState(item?.observation ?? "");
  const [newSub, setNewSub] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const lock = useRef(false);
  const title = `${item ? "Editar" : "Adicionar"} ${direction === "IN" ? "receita" : "saída"}`;
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (lock.current) return;
    const decimal = amount.trim().replace(",", ".");
    if (!description.trim()) { setError("Informe uma descrição válida."); return; }
    if (!/^\d{1,12}(\.\d{1,2})?$/.test(decimal) || !/[1-9]/.test(decimal)) {
      setError("Informe um valor maior que zero, com até duas casas decimais. Exemplo: 1500,00."); return;
    }
    const [year, month] = competence.split("-").map(Number);
    if (!year || year < 1900 || year > 2100 || !month || month > 12) { setError("Informe uma competência válida entre 1900 e 2100."); return; }
    lock.current = true; setBusy(true); setError("");
    try {
      const data = { transaction_date: date, competence_month: month, competence_year: year, description: description.trim(), amount: decimal,
        main_category: category, subcategory_id: subcategory ? Number(subcategory) : null, observation: observation || null };
      onSaved(await api<Transaction>(item ? `/transactions/${item.id}` : `/periods/${period.id}/transactions`, item ? "PATCH" : "POST", item ? data : { ...data, direction }));
    } catch (err) { setError(errorMessage(err)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <>
    <Modal title={title} busy={busy} onClose={onClose}>
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          <div className="form-row">
            <label>Data<input type="date" required value={date} onChange={e => setDate(e.target.value)} /></label>
            <label>Competência<input type="month" required min="1900-01" max="2100-12" value={competence} onChange={e => setCompetence(e.target.value)} /></label>
          </div>
          {company.guided_mode && <p className="help">Data: quando a movimentação ocorreu.<br />Competência: mês ao qual economicamente o lançamento pertence.</p>}
          <label>Descrição<input required maxLength={500} value={description} onChange={e => setDescription(e.target.value)} /></label>
          <div className="form-row">
            <label>Valor<input required inputMode="decimal" placeholder="1500,00" value={amount} onChange={e => setAmount(e.target.value)} /></label>
            <label>Categoria<select aria-label="Categoria" value={category} onChange={e => { setCategory(e.target.value as Category); setSubcategory(""); }}>
              {directionCategories[direction].map(key => <option key={key} value={key}>{categoryLabels[key]}</option>)}
            </select></label>
          </div>
          {company.guided_mode && categoryHelp[category] && <p className="help">{categoryHelp[category]}</p>}
          <label>Subcategoria<select aria-label="Subcategoria" value={subcategory} onChange={e => setSubcategory(e.target.value)}>
            <option value="">Sem subcategoria</option>
            {subcategories.filter(s => s.main_category === category && (s.active || s.id === item?.subcategory_id)).map(s => <option key={s.id} value={s.id}>{s.name}{!s.active ? " (arquivada)" : ""}</option>)}
          </select></label>
          <button type="button" className="text-button" onClick={() => setNewSub(true)}>+ Criar nova subcategoria</button>
          <label>Observação<textarea maxLength={2000} value={observation} onChange={e => setObservation(e.target.value)} /></label>
        </fieldset>
        {error && <p className="error" role="alert">{error}</p>}
        <div className="actions"><button className="primary" disabled={busy}>{busy ? "Salvando…" : "Salvar"}</button><button type="button" disabled={busy} onClick={onClose}>Cancelar</button></div>
      </form>
    </Modal>
    {newSub && <SubcategoryEditor companyId={company.id} fixedCategory={category} onClose={() => setNewSub(false)} onSaved={sub => { onSubcategory(sub); setSubcategory(String(sub.id)); setNewSub(false); }} />}
  </>;
}
