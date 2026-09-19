import { useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import type { Company, Period } from "../types";
import { months } from "../types";
import { categoryLabels, cents, money, errorMessage } from "../types/manual";
import type { Direction, Subcategory, Transaction } from "../types/manual";
import { TransactionEditor } from "../components/TransactionEditor";
import { Modal } from "../components/Modal";
export function Transactions({ company, period, direction }: { company: Company; period: Period; direction: Direction }) {
  const [items, setItems] = useState<Transaction[]>([]), [subs, setSubs] = useState<Subcategory[]>([]);
  const [loading, setLoading] = useState(true), [error, setError] = useState("");
  const [editor, setEditor] = useState<Transaction | "new" | null>(null);
  const [deleting, setDeleting] = useState<Transaction | null>(null), [busy, setBusy] = useState(false);
  const [query, setQuery] = useState(""), [filter, setFilter] = useState("ALL");
  const lock = useRef(false);
  async function load() {
    setLoading(true); setError("");
    try {
      const [transactions, subcategories] = await Promise.all([
        api<Transaction[]>(`/periods/${period.id}/${direction === "IN" ? "revenues" : "expenses"}`),
        api<Subcategory[]>(`/companies/${company.id}/subcategories`),
      ]);
      setItems(transactions); setSubs(subcategories);
    } catch (err) { setError(errorMessage(err)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [period.id, direction]);
  async function remove() {
    if (!deleting || lock.current) return;
    lock.current = true; setBusy(true); setError("");
    try { await api(`/transactions/${deleting.id}`, "DELETE"); setItems(items.filter(t => t.id !== deleting.id)); setDeleting(null); }
    catch (err) { setError(errorMessage(err)); }
    finally { lock.current = false; setBusy(false); }
  }
  const visible = items.filter(t => t.description.toLocaleLowerCase().includes(query.toLocaleLowerCase()) && (filter === "ALL" || t.classification_status === filter));
  return <>
    <span className="eyebrow">LANÇAMENTOS MANUAIS</span>
    <h1>{direction === "IN" ? "Receitas" : "Saídas"} — {months[period.month - 1]}/{period.year}</h1>
    {loading ? <p role="status">Carregando lançamentos…</p> : <>
      <div className="summary"><section className="card"><h2>Total lançado</h2><strong>{money(items.reduce((sum, t) => sum + cents(t.amount), 0n), company.currency)}</strong></section><section className="card"><h2>Quantidade de lançamentos</h2><strong>{items.length}</strong></section></div>
      <div className="toolbar"><button className="primary" disabled={period.status === "closed"} onClick={() => setEditor("new")}>Adicionar {direction === "IN" ? "receita" : "saída"}</button>
        <label>Buscar por descrição<input type="search" value={query} onChange={e => setQuery(e.target.value)} /></label>
        <label>Filtrar status<select aria-label="Filtrar status" value={filter} onChange={e => setFilter(e.target.value)}><option value="ALL">Todos</option><option value="CONFIRMED">Classificados</option><option value="PENDING">Não classificados</option></select></label>
      </div>
      <div className="table-wrap"><table><thead><tr>{["Data", "Competência", "Descrição", "Valor", "Categoria", "Subcategoria", "Status", "Ações"].map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>
        {visible.map(t => <tr key={t.id}>
          <td>{t.transaction_date.split("-").reverse().join("/")}</td><td>{String(t.competence_month).padStart(2, "0")}/{t.competence_year}</td><td>{t.description}</td><td className="amount">{money(cents(t.amount), company.currency)}</td>
          <td>{categoryLabels[t.main_category]}</td><td>{subs.find(s => s.id === t.subcategory_id)?.name ?? "—"}</td><td><span className={`status ${t.classification_status === "PENDING" ? "pending" : ""}`}>{t.classification_status === "CONFIRMED" ? "Classificado" : "Não classificado"}</span></td>
          <td><div className="actions"><button disabled={period.status === "closed"} onClick={() => setEditor(t)}>Editar</button><button disabled={period.status === "closed"} onClick={() => { setError(""); setDeleting(t); }}>Excluir</button></div></td>
        </tr>)}
      </tbody></table>{visible.length === 0 && <p className="empty">Nenhum lançamento encontrado.</p>}</div>
    </>}
    {error && !deleting && <div role="alert" className="error">{error}<button onClick={() => void load()}>Tentar novamente</button></div>}
    {editor && <TransactionEditor company={company} period={period} direction={direction} item={editor === "new" ? undefined : editor} subcategories={subs} onSubcategory={sub => setSubs([...subs, sub])} onClose={() => setEditor(null)} onSaved={t => { setItems([t, ...items.filter(x => x.id !== t.id)]); setEditor(null); }} />}
    {deleting && <Modal title="Excluir lançamento" busy={busy} onClose={() => setDeleting(null)}><p>Excluir “{deleting.description}”? Esta ação não pode ser desfeita.</p>{error && <p role="alert" className="error">{error}</p>}<div className="actions"><button className="danger" disabled={busy} onClick={() => void remove()}>Confirmar exclusão</button><button disabled={busy} onClick={() => setDeleting(null)}>Cancelar</button></div></Modal>}
  </>;
}
