import { useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import { categoryLabels, errorMessage } from "../types/manual";
import type { Category, Subcategory } from "../types/manual";
import { SubcategoryEditor } from "./SubcategoryEditor";
import { Modal } from "./Modal";
export function Subcategories({ companyId }: { companyId: number }) {
  const [items, setItems] = useState<Subcategory[]>([]), [filter, setFilter] = useState("");
  const [editor, setEditor] = useState<Subcategory | "new" | null>(null), [archive, setArchive] = useState<Subcategory | null>(null);
  const [error, setError] = useState(""), [busy, setBusy] = useState(false), [loading, setLoading] = useState(true);
  const lock = useRef(false);
  async function load() {
    setLoading(true); setError("");
    try { setItems(await api<Subcategory[]>(`/companies/${companyId}/subcategories`)); }
    catch (err) { setError(errorMessage(err)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [companyId]);
  async function doArchive() {
    if (!archive || lock.current) return;
    lock.current = true; setBusy(true); setError("");
    try { const saved = await api<Subcategory>(`/subcategories/${archive.id}/archive`, "POST"); setItems(items.map(s => s.id === saved.id ? saved : s)); setArchive(null); }
    catch (err) { setError(errorMessage(err)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <section className="card subcategories"><h2>Categorias e Subcategorias</h2><p>As categorias principais são fixas. Personalize as subcategorias da sua empresa.</p>
    <div className="toolbar"><label>Categoria principal<select aria-label="Categoria principal" value={filter} onChange={e => setFilter(e.target.value)}><option value="">Todas</option>{(Object.keys(categoryLabels) as Category[]).map(k => <option key={k} value={k}>{categoryLabels[k]}</option>)}</select></label><button onClick={() => setEditor("new")}>+ Criar nova subcategoria</button></div>
    {loading ? <p role="status">Carregando subcategorias…</p> : <div className="table-wrap"><table><thead><tr><th>Nome</th><th>Categoria</th><th>Tipo</th><th>Status</th><th>Ações</th></tr></thead><tbody>{items.filter(s => !filter || s.main_category === filter).map(s => <tr key={s.id}><td>{s.name}</td><td>{categoryLabels[s.main_category]}</td><td>{s.is_default ? "Padrão" : "Personalizada"}</td><td>{s.active ? "Ativa" : "Arquivada"}</td><td><div className="actions">{!s.is_default && <button onClick={() => setEditor(s)}>Editar</button>}<button disabled={!s.active} onClick={() => { setError(""); setArchive(s); }}>Arquivar</button></div></td></tr>)}</tbody></table></div>}
    {error && !archive && <p role="alert" className="error">{error}<button onClick={() => void load()}>Tentar novamente</button></p>}
    {editor && <SubcategoryEditor companyId={companyId} item={editor === "new" ? undefined : editor} onClose={() => setEditor(null)} onSaved={s => { setItems([...items.filter(x => x.id !== s.id), s]); setEditor(null); }} />}
    {archive && <Modal title="Arquivar subcategoria" busy={busy} onClose={() => setArchive(null)}><p>Arquivar “{archive.name}”? Os lançamentos existentes manterão essa informação.</p>{error && <p role="alert" className="error">{error}</p>}<button disabled={busy} onClick={() => void doArchive()}>Confirmar arquivamento</button></Modal>}
  </section>;
}
