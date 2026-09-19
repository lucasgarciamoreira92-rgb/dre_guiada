export function Sidebar({
  page,
  onNavigate,
}: {
  page: string;
  onNavigate: (p: "overview" | "settings") => void;
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
        {[
          "Receitas",
          "Saídas",
          "Informações Complementares",
          "Pendências",
          "DRE",
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
