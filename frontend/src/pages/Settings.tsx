import { Subcategories } from "../components/Subcategories";
import { useState } from "react";
import type { Company } from "../types";
import { api } from "../services/api";
export function Settings({
  company,
  onChange,
}: {
  company: Company;
  onChange: (c: Company) => void;
}) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function toggle() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      onChange(
        await api<Company>(`/companies/${company.id}`, "PATCH", {
          guided_mode: !company.guided_mode,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível salvar.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <span className="eyebrow">PREFERÊNCIAS</span>
      <h1>Configurações</h1>
      <section className="card">
        <h2>Dados da empresa</h2>
        <dl>
          <dt>Nome</dt>
          <dd>{company.name}</dd>
          <dt>CNPJ</dt>
          <dd>{company.cnpj || "Não informado"}</dd>
          <dt>Segmento</dt>
          <dd>{company.segment || "Não informado"}</dd>
          <dt>Moeda</dt>
          <dd>{company.currency}</dd>
        </dl>
        <hr />
        <div className="toggle-row">
          <div>
            <h2>Modo Guiado</h2>
            {company.guided_mode && (
              <p>Exibe explicações para ajudar você em cada etapa.</p>
            )}
          </div>
          <button
            role="switch"
            aria-label="Modo Guiado"
            aria-checked={company.guided_mode}
            disabled={busy}
            onClick={toggle}
          >
            {busy ? "Salvando…" : company.guided_mode ? "ON" : "OFF"}
          </button>
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </section>
      <Subcategories companyId={company.id} />
    </>
  );
}
