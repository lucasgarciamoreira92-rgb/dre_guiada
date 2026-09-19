export type Direction = "IN" | "OUT";
export type Category = "REVENUE_RECURRING" | "REVENUE_SERVICE" | "REVENUE_PRODUCT" | "REVENUE_OTHER_OPERATING" | "FINANCIAL_REVENUE" | "NON_DRE" | "UNDEFINED" | "COST" | "EXPENSE" | "INVESTMENT" | "FINANCIAL_EXPENSE" | "TAX";
export interface Subcategory {
  id: number; company_id: number; main_category: Category; name: string;
  description: string | null; active: boolean; is_default: boolean;
}
export interface Transaction {
  id: number; company_id: number; period_id: number; direction: Direction;
  transaction_date: string; competence_month: number; competence_year: number;
  description: string; original_description: string; amount: string;
  main_category: Category; subcategory_id: number | null; observation: string | null;
  classification_status: "CONFIRMED" | "PENDING"; dre_effect: string;
  include_in_dre: boolean; origin_type: "MANUAL";
}
export const categoryLabels: Record<Category, string> = {
  REVENUE_RECURRING: "Receita recorrente", REVENUE_SERVICE: "Receita de serviços",
  REVENUE_PRODUCT: "Receita de produtos/equipamentos", REVENUE_OTHER_OPERATING: "Outras receitas operacionais",
  FINANCIAL_REVENUE: "Receita financeira", NON_DRE: "Não compõe DRE", UNDEFINED: "Não sei / revisar",
  COST: "Custo", EXPENSE: "Despesa", INVESTMENT: "Investimento", FINANCIAL_EXPENSE: "Despesa financeira", TAX: "Tributo",
};
export const directionCategories: Record<Direction, Category[]> = {
  IN: ["REVENUE_RECURRING", "REVENUE_SERVICE", "REVENUE_PRODUCT", "REVENUE_OTHER_OPERATING", "FINANCIAL_REVENUE", "NON_DRE", "UNDEFINED"],
  OUT: ["COST", "EXPENSE", "INVESTMENT", "FINANCIAL_EXPENSE", "TAX", "NON_DRE", "UNDEFINED"],
};
export const categoryHelp: Partial<Record<Category, string>> = {
  COST: "Gasto diretamente relacionado à entrega do produto ou serviço.",
  EXPENSE: "Gasto necessário para manter a empresa funcionando.",
  INVESTMENT: "Saída destinada a algo que tende a gerar benefício por mais de um período.",
  TAX: "O efeito deste tributo na DRE será definido em uma etapa futura.",
};
export function cents(amount: string): bigint {
  const [integer, fraction = ""] = amount.split(".");
  return BigInt(integer) * 100n + BigInt(fraction.padEnd(2, "0"));
}
export function money(value: bigint, currency: string): string {
  return `${currency === "BRL" ? "R$" : currency} ${(value / 100n).toLocaleString("pt-BR")},${(value % 100n).toString().padStart(2, "0")}`;
}
export const errorMessage = (error: unknown) => error instanceof Error ? error.message : "Não foi possível concluir. Tente novamente.";
