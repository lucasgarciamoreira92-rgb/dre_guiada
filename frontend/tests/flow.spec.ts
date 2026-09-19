import { test, expect } from "@playwright/test";
async function fill(page: import("@playwright/test").Page) {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Monte sua DRE de forma simples" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Começar minha DRE" }).click();
  await page.getByLabel("Nome da empresa").fill("Empresa Teste DRE");
  await page.getByLabel("Segmento").fill("Serviços");
  await page.getByLabel("Mês", { exact: true }).selectOption("8");
  await page.getByLabel("Ano", { exact: true }).fill("2026");
}
test("complete flow, persistence, guided mode and responsive layout", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await fill(page);
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "DRE — Agosto/2026" }),
  ).toBeVisible();
  for (const [label, value] of [
    ["Receitas", "0%"],
    ["Saídas", "0%"],
    ["Informações complementares", "Ajustes manuais"],
    ["Pendências", "0"],
    ["DRE", "Calculada"],
  ]) {
    const card = page
      .locator("section")
      .filter({ has: page.getByRole("heading", { name: label, exact: true }) });
    await expect(card.locator("strong")).toHaveText(value);
  }
  await expect(
    page.getByRole("button", { name: "Começar pelas Receitas" }),
  ).toBeEnabled();
  const id = new URL(page.url()).searchParams.get("period");
  const p = (await (await request.get(`/api/periods/${id}`)).json()).data;
  expect(p).toMatchObject({
    month: 8,
    year: 2026,
    status: "draft",
    completion_percentage: 0,
  });
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "DRE — Agosto/2026" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Configurações" }).click();
  await page.getByRole("switch", { name: "Modo Guiado" }).click();
  await expect(page.getByRole("switch")).toHaveAttribute(
    "aria-checked",
    "false",
  );
  await page.reload();
  await expect(page.locator(".help")).toHaveCount(0);
  await page.getByRole("button", { name: "Configurações" }).click();
  await expect(page.getByRole("switch")).toHaveAttribute(
    "aria-checked",
    "false",
  );
  await page.getByRole("switch").click();
  await expect(page.getByRole("switch")).toHaveAttribute(
    "aria-checked",
    "true",
  );
  await page.getByRole("button", { name: "Visão Geral" }).click();
  await expect(page.locator(".help")).toBeVisible();
  await page.screenshot({
    path: "test-results/overview-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/overview-mobile.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
test("retry period without recreating company and prevent double submit", async ({
  page,
}) => {
  let companies = 0,
    periods = 0;
  await page.route("**/api/companies", async (route) => {
    if (route.request().method() === "POST") companies++;
    await route.continue();
  });
  await page.route("**/api/companies/*/periods", async (route) => {
    if (route.request().method() === "POST") {
      periods++;
      if (periods === 1) {
        await route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "UNAVAILABLE",
              message: "Tente novamente.",
              details: {},
            },
          }),
        });
        return;
      }
    }
    await route.continue();
  });
  await fill(page);
  await page
    .getByRole("button", { name: "Continuar", exact: true })
    .evaluate((button: HTMLButtonElement) => {
      button.click();
      button.click();
    });
  await expect(page.getByRole("alert")).toHaveText("Tente novamente.");
  expect(companies).toBe(1);
  expect(periods).toBe(1);
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "DRE — Agosto/2026" }),
  ).toBeVisible();
  expect(companies).toBe(1);
  expect(periods).toBe(2);
});
test("friendly validation errors", async ({ page }) => {
  await fill(page);
  await page.getByLabel("Nome da empresa").fill("   ");
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveText(
    "Informe o nome da empresa.",
  );
  await page.goto("/?period=999999");
  await expect(page.getByRole("alert")).toHaveText("Período não encontrado.");
});
