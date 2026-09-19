import { test, expect } from "@playwright/test";
import type { Page, APIRequestContext } from "@playwright/test";

async function setup(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Começar minha DRE" }).click();
  await page.getByLabel("Nome da empresa").fill("Empresa Teste DRE");
  await page.getByLabel("Mês", { exact: true }).selectOption("8");
  await page.getByLabel("Ano", { exact: true }).fill("2026");
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "DRE — Agosto/2026" })).toBeVisible();
  return new URL(page.url()).searchParams.get("period")!;
}
async function add(page: Page, area: "Receitas" | "Saídas", description: string, amount: string, category: string, subcategory?: string) {
  await page.getByRole("button", { name: area, exact: true }).click();
  await page.getByRole("button", { name: area === "Receitas" ? "Adicionar receita" : "Adicionar saída", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Data", { exact: true }).fill(area === "Receitas" ? "2026-09-05" : "2026-08-10");
  await dialog.getByLabel("Competência", { exact: true }).fill("2026-08");
  await dialog.getByLabel("Descrição", { exact: true }).fill(description);
  await dialog.getByLabel("Valor", { exact: true }).fill(amount);
  await dialog.getByLabel("Categoria", { exact: true }).selectOption(category);
  if (subcategory) await dialog.getByLabel("Subcategoria", { exact: true }).selectOption({ label: subcategory });
  await dialog.getByRole("button", { name: "Salvar", exact: true }).click();
  await expect(dialog).not.toBeVisible();
}
async function apiTransaction(request: APIRequestContext, periodId: string | number, values: Record<string, unknown> = {}) {
  const response = await request.post(`/api/periods/${periodId}/transactions`, { data: {
    direction: "IN", description: "Receita", transaction_date: "2026-09-05", competence_month: 8, competence_year: 2026,
    amount: "100000", main_category: "REVENUE_SERVICE", ...values,
  } });
  expect(response.status()).toBe(201);
  return (await response.json()).data;
}

test("required four entries produce DRE and dashboard, with drilldown and guided mode", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await setup(page);
  await add(page, "Receitas", "Mensalidades", "100000", "REVENUE_RECURRING");
  await add(page, "Saídas", "Link IP", "20000", "COST", "Infraestrutura");
  await add(page, "Saídas", "Google Workspace", "1500", "EXPENSE", "Tecnologia");
  await add(page, "Saídas", "Servidor", "30000", "INVESTMENT", "Equipamentos");
  await page.getByRole("button", { name: "DRE", exact: true }).click();
  const expected = { gross_revenue: "R$ 100.000,00", revenue_deductions: "R$ 0,00", net_revenue: "R$ 100.000,00", costs: "R$ 20.000,00", gross_result: "R$ 80.000,00", operating_expenses: "R$ 1.500,00", operating_result: "R$ 78.500,00", net_result: "R$ 78.500,00" };
  for (const [line, value] of Object.entries(expected)) await expect(page.locator(`[data-line="${line}"] .dre-value`)).toHaveText(value);
  await expect(page.locator('[data-margin="gross"] strong')).toHaveText("80,00%");
  await expect(page.locator('[data-margin="operating"] strong')).toHaveText("78,50%");
  await expect(page.locator('[data-margin="net"] strong')).toHaveText("78,50%");
  await expect(page.getByText("Calculada", { exact: true })).toBeVisible();
  await expect(page.getByText("Servidor", { exact: true })).toHaveCount(0);
  await expect(page.locator('.dre-line .guide-note')).toHaveCount(4);
  await page.getByRole("button", { name: "Detalhar Custos", exact: true }).click();
  const panel = page.getByRole("dialog", { name: "Detalhamento — Custos", exact: true });
  await expect(panel.locator('.detail-groups')).toContainText("Infraestrutura");
  await expect(panel.locator('.detail-groups')).toContainText("R$ 20.000,00");
  await expect(panel.getByText("Link IP", { exact: true })).toBeVisible();
  await expect(panel.getByRole("button", { name: "Editar", exact: true })).toHaveCount(0);
  await panel.getByRole("link", { name: "Abrir registro de origem" }).click();
  await expect(page.getByRole("heading", { name: "Saídas — Agosto/2026" })).toBeVisible();
  await expect(page.getByRole("row").filter({ hasText: "Link IP" })).toBeVisible();
  await page.getByRole("button", { name: "Configurações" }).click();
  await page.getByRole("switch", { name: "Modo Guiado" }).click();
  await expect(page.getByRole("switch")).toHaveAttribute("aria-checked", "false");
  await page.getByRole("button", { name: "DRE", exact: true }).click();
  await expect(page.locator('[data-line="net_result"] .dre-value')).toHaveText("R$ 78.500,00");
  await expect(page.locator('.guide-note')).toHaveCount(0);
  await page.screenshot({ path: "test-results/m3-dre-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/m3-dre-mobile.png", fullPage: true });
  await page.getByRole("button", { name: "Visão Geral" }).click();
  for (const [label, value] of [["Receita Líquida", "R$ 100.000,00"], ["Custos", "R$ 20.000,00"], ["Despesas", "R$ 1.500,00"], ["Resultado Líquido", "R$ 78.500,00"], ["Margem Líquida", "78,50%"]]) {
    const card = page.locator('.dashboard-results section').filter({ has: page.getByRole("heading", { name: label, exact: true }) });
    await expect(card.locator('strong')).toHaveText(value);
  }
  expect(errors).toEqual([]);
});

test("explicit deductions and profit tax calculate scenario two; other adjustment stays pending", async ({ page, request }) => {
  const id = await setup(page);
  for (const values of [{}, { direction: "OUT", main_category: "COST", amount: "30000" }, { direction: "OUT", main_category: "EXPENSE", amount: "20000" }, { main_category: "FINANCIAL_REVENUE", amount: "2000" }, { direction: "OUT", main_category: "FINANCIAL_EXPENSE", amount: "1000" }]) await apiTransaction(request, id, values);
  await page.getByRole("button", { name: "Informações Complementares", exact: true }).click();
  await page.getByLabel("Tipo de ajuste").selectOption("REVENUE_DEDUCTION");
  await page.getByLabel("Tipo de dedução").selectOption("REVENUE_TAX");
  await page.getByLabel("Valor", { exact: true }).fill("10000");
  await page.getByLabel("Justificativa").fill("Impostos sobre receita informados");
  await page.getByRole("button", { name: "Salvar ajuste" }).click();
  await expect(page.locator('.adjustment-list')).toContainText("R$ 10.000,00");
  await page.getByLabel("Tipo de ajuste").selectOption("PROFIT_TAX");
  await page.getByLabel("Valor", { exact: true }).fill("5000");
  await page.getByLabel("Justificativa").fill("Tributos sobre lucro apurados");
  await page.getByRole("button", { name: "Salvar ajuste" }).click();
  await expect(page.locator('.adjustment-list')).toContainText("R$ 5.000,00");
  await page.getByRole("button", { name: "DRE", exact: true }).click();
  for (const [line, amount] of Object.entries({ net_revenue: "R$ 90.000,00", gross_result: "R$ 60.000,00", operating_result: "R$ 40.000,00", financial_result: "R$ 1.000,00", result_before_tax: "R$ 41.000,00", profit_taxes: "R$ 5.000,00", net_result: "R$ 36.000,00" })) await expect(page.locator(`[data-line="${line}"] .dre-value`)).toHaveText(amount);
  for (const [key, value] of Object.entries({ gross: "66,67%", operating: "44,44%", net: "40,00%" })) await expect(page.locator(`[data-margin="${key}"] strong`)).toHaveText(value);
  await page.getByRole("button", { name: "Detalhar Deduções", exact: true }).click();
  await expect(page.getByRole("dialog").locator('.detail-groups')).toContainText("Impostos sobre receita");
  await page.getByRole("button", { name: "Fechar Detalhamento — Deduções", exact: true }).click();
  await page.getByRole("button", { name: "Informar ajustes do período" }).click();
  await page.getByLabel("Tipo de ajuste").selectOption("OTHER_ADJUSTMENT");
  await page.getByLabel("Valor", { exact: true }).fill("999");
  await page.getByLabel("Justificativa").fill("Sem regra definida");
  await page.getByRole("button", { name: "Salvar ajuste" }).click();
  await expect(page.locator('.adjustment-list')).toContainText("Pendente — fora da DRE");
  await page.getByRole("button", { name: "DRE", exact: true }).click();
  await expect(page.getByText("Provisória", { exact: true })).toBeVisible();
  await expect(page.locator('[data-line="net_result"] .dre-value')).toHaveText("R$ 36.000,00");
});

test("zero revenue, negative cents and pending transactions display without invalid numbers", async ({ page, request }) => {
  const id = await setup(page);
  await apiTransaction(request, id, { direction: "OUT", main_category: "COST", amount: "0.55" });
  await apiTransaction(request, id, { main_category: "UNDEFINED", amount: "1000" });
  await page.getByRole("button", { name: "DRE", exact: true }).click();
  await expect(page.locator('[data-line="net_result"] .dre-value')).toHaveText("−R$ 0,55");
  await expect(page.locator('[data-margin="net"] strong')).toHaveText("Não aplicável");
  await expect(page.locator('.notice')).toContainText("1 lançamento(s)");
  await expect(page.getByText("Provisória", { exact: true })).toBeVisible();
  await expect(page.getByText(/NaN|Infinity/)).toHaveCount(0);
  await page.getByRole("button", { name: "Detalhar Receita Bruta", exact: true }).click();
  await expect(page.getByRole("dialog").getByText("Nenhum registro compõe esta linha.")).toBeVisible();
});

test("competence crosses source periods and the origin link opens the actual source", async ({ page, request }) => {
  const august = await setup(page);
  const { data: p } = await (await request.get(`/api/periods/${august}`)).json();
  const { data: september } = await (await request.post(`/api/companies/${p.company_id}/periods`, { data: { month: 9, year: 2026 } })).json();
  await apiTransaction(request, september.id, { description: "Receita de agosto paga em setembro" });
  await page.getByRole("button", { name: "DRE", exact: true }).click();
  await expect(page.locator('[data-line="gross_revenue"] .dre-value')).toHaveText("R$ 100.000,00");
  await page.getByRole("button", { name: "Detalhar Receita Bruta", exact: true }).click();
  await page.getByRole("dialog").getByRole("link", { name: "Abrir registro de origem" }).click();
  await expect(page.getByRole("heading", { name: "Receitas — Setembro/2026" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Receita de agosto paga em setembro" })).toBeVisible();
  await page.getByRole("button", { name: "DRE", exact: true }).click();
  await expect(page.locator('[data-line="gross_revenue"] .dre-value')).toHaveText("R$ 0,00");
});
