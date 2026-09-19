import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../services/api";
import { months } from "../types";
import type { Company, Period } from "../types";
export function Setup({ onDone }: { onDone: (c: Company, p: Period) => void }) {
  const [name, setName] = useState(""),
    [cnpj, setCnpj] = useState(""),
    [segment, setSegment] = useState("");
  const [month, setMonth] = useState(new Date().getMonth() + 1),
    [year, setYear] = useState(new Date().getFullYear());
  const [company, setCompany] = useState<Company | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const lock = useRef(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (lock.current) return;
    if (!name.trim()) {
      setError("Informe o nome da empresa.");
      return;
    }
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const c =
        company ??
        (await api<Company>("/companies", "POST", {
          name: name.trim(),
          cnpj: cnpj.trim() || null,
          segment: segment.trim() || null,
        }));
      setCompany(c);
      let p: Period;
      try {
        p = await api<Period>(`/companies/${c.id}/periods`, "POST", {
          month,
          year,
        });
      } catch (err) {
        if (!(err instanceof ApiError) || err.code !== "PERIOD_ALREADY_EXISTS")
          throw err;
        const existing = (
          await api<Period[]>(`/companies/${c.id}/periods`)
        ).find((p) => p.month === month && p.year === year);
        if (!existing) throw err;
        p = existing;
      }
      onDone(c, p);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Não foi possível continuar.",
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <main className="setup">
      <span className="eyebrow">VAMOS COMEÇAR</span>
      <h1>Sua empresa, seu período.</h1>
      <p className="intro">
        Preencha os dados básicos para organizar sua primeira DRE.
      </p>
      <form onSubmit={submit} className="card">
        <fieldset disabled={busy || !!company}>
          <legend>Dados da empresa</legend>
          <label>
            Nome da empresa
            <input
              required
              maxLength={200}
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="organization"
            />
          </label>
          <div className="form-row">
            <label>
              CNPJ <small>opcional</small>
              <input
                maxLength={18}
                value={cnpj}
                onChange={(e) => setCnpj(e.target.value)}
              />
            </label>
            <label>
              Segmento <small>opcional</small>
              <input
                maxLength={120}
                value={segment}
                onChange={(e) => setSegment(e.target.value)}
              />
            </label>
          </div>
        </fieldset>
        <fieldset disabled={busy}>
          <legend>Período</legend>
          <div className="form-row">
            <label>
              <span id="month-label">Mês</span>
              <select
                aria-labelledby="month-label"
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
              >
                {months.map((m, i) => (
                  <option key={m} value={i + 1}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Ano
              <input
                type="number"
                required
                min={1900}
                max={2100}
                step={1}
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
              />
            </label>
          </div>
        </fieldset>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {company && error && (
          <p>Sua empresa já foi salva. Tente continuar para criar o período.</p>
        )}
        <button className="primary" disabled={busy}>
          {busy ? "Salvando…" : "Continuar"}
        </button>
      </form>
    </main>
  );
}
