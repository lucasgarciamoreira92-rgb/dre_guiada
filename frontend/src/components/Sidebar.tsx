export function Sidebar({
  page,
  onNavigate,
}: {
  page: string;
  onNavigate: (p: "overview" | "settings" | "revenues" | "expenses" | "dre" | "adjustments") => void;
}) {
  return (
    <aside>
      <div className="brand">
        <span className="brand-icon">D</span>DRE Guiada
      </div>
      <span className="eyebrow">SEU FECHAMENTO</span>
      <nav aria-label="Menu principal">
        <button
          className={page === "overview" ? "active" : ""}
          onClick={() => onNavigate("overview")}
        >
          Visão Geral
        </button>
        <button className={page === "revenues" ? "active" : ""} onClick={() => onNavigate("revenues")}>Receitas</button>
        <button className={page === "expenses" ? "active" : ""} onClick={() => onNavigate("expenses")}>Saídas</button>
        <button className={page === "adjustments" ? "active" : ""} onClick={() => onNavigate("adjustments")}>Informações Complementares</button>
        <button className={page === "dre" ? "active" : ""} onClick={() => onNavigate("dre")}>DRE</button>
        {[
          "Pendências",
        ].map((x) => (
          <button disabled key={x} title="Disponível em um próximo marco">
            {x}
            <small>Em breve</small>
          </button>
        ))}
        <button
          className={page === "settings" ? "active" : ""}
          onClick={() => onNavigate("settings")}
        >
          Configurações
        </button>
      </nav>
      <p className="sidebar-foot">
        Simplicidade para entender.
        <br />
        Clareza para decidir.
      </p>
    </aside>
  );
}
