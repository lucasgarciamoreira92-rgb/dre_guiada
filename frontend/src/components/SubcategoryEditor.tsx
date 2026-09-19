import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import { categoryLabels, errorMessage } from "../types/manual";
import type { Category, Subcategory } from "../types/manual";
import { Modal } from "./Modal";
export function SubcategoryEditor({ companyId, fixedCategory, item, onSaved, onClose }: {
  companyId: number; fixedCategory?: Category; item?: Subcategory;
  onSaved: (sub: Subcategory) => void; onClose: () => void;
}) {
  const [name, setName] = useState(item?.name ?? "");
  const [description, setDescription] = useState(item?.description ?? "");
  const [category, setCategory] = useState<Category>(fixedCategory ?? item?.main_category ?? "COST");
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const lock = useRef(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (lock.current) return;
    if (!name.trim()) { setError("Informe o nome da subcategoria."); return; }
    lock.current = true; setBusy(true); setError("");
    try {
      const saved = await api<Subcategory>(item ? `/subcategories/${item.id}` : `/companies/${companyId}/subcategories`, item ? "PATCH" : "POST", {
        name, description: description || null, main_category: category,
      });
      onSaved(saved);
    } catch (err) { setError(errorMessage(err)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <Modal title={item ? "Editar subcategoria" : "Nova subcategoria"} onClose={onClose} busy={busy}>
    <form onSubmit={submit}>
      <fieldset disabled={busy}>
        <label>Nome<input required maxLength={200} value={name} onChange={e => setName(e.target.value)} /></label>
        <label>Categoria principal<select aria-label="Categoria principal" disabled={!!fixedCategory} value={category} onChange={e => setCategory(e.target.value as Category)}>
          {(Object.keys(categoryLabels) as Category[]).map(key => <option value={key} key={key}>{categoryLabels[key]}</option>)}
        </select></label>
        <label>Descrição opcional<textarea maxLength={1000} value={description} onChange={e => setDescription(e.target.value)} /></label>
      </fieldset>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="primary" disabled={busy}>{busy ? "Salvando…" : "Salvar subcategoria"}</button>
    </form>
  </Modal>;
}
