import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Welcome } from "./pages/Welcome";
import { Setup } from "./pages/Setup";
import { Overview } from "./pages/Overview";
import { Settings } from "./pages/Settings";
import { Sidebar } from "./components/Sidebar";
import { api } from "./services/api";
import type { Company, Period } from "./types";
import "./styles/app.css";
function App() {
  const [page, setPage] = useState<
    "welcome" | "setup" | "overview" | "settings"
  >("welcome");
  const [company, setCompany] = useState<Company | null>(null),
    [period, setPeriod] = useState<Period | null>(null);
  const [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  async function restore() {
    setLoading(true);
    setError("");
    const id = new URLSearchParams(location.search).get("period");
    try {
      if (id) {
        const p = await api<Period>(`/periods/${encodeURIComponent(id)}`);
        const c = await api<Company>(`/companies/${p.company_id}`);
        setPeriod(p);
        setCompany(c);
        setPage("overview");
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível abrir o período.",
      );
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void restore();
  }, []);
  function done(c: Company, p: Period) {
    setCompany(c);
    setPeriod(p);
    history.replaceState(null, "", `?period=${p.id}`);
    setPage("overview");
  }
  if (loading)
    return (
      <main className="setup">
        <p role="status">Carregando…</p>
      </main>
    );
  if (error)
    return (
      <main className="setup">
        <p role="alert" className="error">
          {error}
        </p>
        <button onClick={() => void restore()}>Tentar novamente</button>
        <a href="/">Voltar ao início</a>
      </main>
    );
  if (company && period)
    return (
      <div className="layout">
        <Sidebar page={page} onNavigate={setPage} />
        <main className="workspace">
          {page === "settings" ? (
            <Settings company={company} onChange={setCompany} />
          ) : (
            <Overview company={company} period={period} />
          )}
        </main>
      </div>
    );
  return (
    <>
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">D</span>DRE Guiada
        </div>
        <span>Clareza começa aqui.</span>
      </header>
      {page === "welcome" ? (
        <Welcome onStart={() => setPage("setup")} />
      ) : (
        <Setup onDone={done} />
      )}
    </>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
