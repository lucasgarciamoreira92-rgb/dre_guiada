export type DreLine = "gross_revenue" | "revenue_deductions" | "costs" | "operating_expenses" | "financial_revenue" | "financial_expense" | "profit_taxes";
export type ResultLine = DreLine | "net_revenue" | "gross_result" | "operating_result" | "financial_result" | "result_before_tax" | "net_result";
export type Dre = Record<ResultLine, string> & {
  period: { id: number; company_id: number; month: number; year: number; status: string };
  status: "CALCULATED" | "PROVISIONAL";
  margins: { gross: string | null; operating: string | null; net: string | null };
  data_quality: { pending_transactions: number; pending_adjustments: number; has_pending_items: boolean };
};
export interface DreDetails {
  line: DreLine; total: string; count: number; transaction_count: number; adjustment_count: number;
  groups: { subcategory_id: number | null; name: string; total: string; count: number }[];
  items: { source_type: "TRANSACTION" | "ADJUSTMENT"; id: number; period_id: number; direction: "IN" | "OUT" | null; description: string; amount: string; transaction_date: string | null; competence_month: number; competence_year: number }[];
}
export type AdjustmentType = "PROFIT_TAX" | "REVENUE_DEDUCTION" | "OTHER_ADJUSTMENT";
export type DeductionKind = "REVENUE_TAX" | "RETURN" | "DISCOUNT" | "OTHER_APPROVED";
export interface Adjustment {
  id: number; period_id: number; type: AdjustmentType; amount: string; observation: string;
  deduction_kind: DeductionKind | null; status: "PENDING" | "CONFIRMED"; dre_effect: string; created_at: string;
}
export const adjustmentLabels: Record<AdjustmentType, string> = { PROFIT_TAX: "Tributo sobre lucro", REVENUE_DEDUCTION: "Dedução da receita", OTHER_ADJUSTMENT: "Outro ajuste (sem efeito definido)" };
export const deductionLabels: Record<DeductionKind, string> = { REVENUE_TAX: "Impostos sobre receita", RETURN: "Devoluções", DISCOUNT: "Abatimentos", OTHER_APPROVED: "Outras deduções aprovadas" };
export const dreLabels: Record<ResultLine, string> = {
  gross_revenue: "Receita Bruta", revenue_deductions: "Deduções", net_revenue: "Receita Líquida", costs: "Custos", gross_result: "Resultado Bruto",
  operating_expenses: "Despesas Operacionais", operating_result: "Resultado Operacional", financial_revenue: "Receita Financeira", financial_expense: "Despesa Financeira",
  financial_result: "Resultado Financeiro", result_before_tax: "Resultado Antes dos Tributos", profit_taxes: "Tributos sobre Lucro", net_result: "Resultado Líquido",
};
export const guidedText: Partial<Record<ResultLine | "margin_gross" | "margin_operating" | "margin_net", string>> = {
  net_revenue: "Receita após impostos sobre receita, devoluções e outras deduções informadas.",
  gross_result: "O que resta da receita líquida depois dos custos de entrega.",
  operating_result: "Resultado após custos e despesas operacionais, antes do resultado financeiro e dos tributos sobre lucro.",
  net_result: "Resultado após custos, despesas, resultado financeiro e tributos sobre lucro informados.",
  margin_gross: "Quanto resta após os custos para cada R$ 100 de receita líquida.",
  margin_operating: "Quanto resta da operação para cada R$ 100 de receita líquida.",
  margin_net: "Quanto sobra como resultado para cada R$ 100 de receita líquida.",
};
// Presentation only: amounts and percentages are received ready from the backend.
// String formatting preserves cents, negative values and totals beyond Number precision.
export function formatMoney(value: string, currency: string): string {
  const negative = value.startsWith("-");
  const [integer, decimal = "00"] = (negative ? value.slice(1) : value).split(".");
  return `${negative ? "−" : ""}${currency === "BRL" ? "R$" : currency} ${integer.replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${decimal.padEnd(2, "0")}`;
}
export function formatMargin(value: string | null): string {
  return value === null ? "Não aplicável" : `${value.replace(".", ",")}%`;
}
