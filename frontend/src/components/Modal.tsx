import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
export function Modal({ title, onClose, busy = false, children }: { title: string; onClose: () => void; busy?: boolean; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { ref.current?.showModal(); }, []);
  return <dialog ref={ref} aria-label={title} onCancel={e => { e.preventDefault(); if (!busy) onClose(); }}>
    <div className="section-heading"><h2>{title}</h2><button type="button" aria-label={`Fechar ${title}`} disabled={busy} onClick={onClose}>×</button></div>
    {children}
  </dialog>;
}
