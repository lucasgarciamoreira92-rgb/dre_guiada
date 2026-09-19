import { useEffect, useState } from "react";
import type { Dre } from "../types/dre";
import { errorMessage } from "../types/manual";
import { api } from "./api";
export function useDre(periodId: number) {
  const [data, setData] = useState<Dre | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setData(null); setError("");
    api<Dre>(`/periods/${periodId}/dre`)
      .then(result => { if (active) setData(result); })
      .catch(err => { if (active) setError(errorMessage(err)); });
    return () => { active = false; };
  }, [periodId, attempt]);
  return { data, error, retry: () => setAttempt(value => value + 1) };
}
