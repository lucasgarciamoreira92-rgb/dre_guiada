export interface Company {
  id: number;
  name: string;
  cnpj: string | null;
  segment: string | null;
  currency: string;
  guided_mode: boolean;
  created_at: string;
  updated_at: string;
}
export interface Period {
  id: number;
  company_id: number;
  month: number;
  year: number;
  status: "draft" | "provisional" | "ready" | "closed" | "reopened";
  completion_percentage: number;
  created_at: string;
  closed_at: string | null;
  reopened_at: string | null;
}
export const months = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];
