import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

test('complete visible milestone 3.2 flow', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  const directory = process.env.DRE_VISUAL_DIR!;
  await mkdir(directory, { recursive: true });
  async function capture(name: string) {
    await expect(page.getByText(/Carregando|Calculando DRE/)).toHaveCount(0);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: resolve(directory, name + '.png'), fullPage: true, animations: 'disabled' });
    // Keep each stage visible on the desktop and in the recorded video.
    await page.waitForTimeout(1500);
  }
  async function add(description: string, amount: string, category: string, subcategory?: string) {
    await page.getByRole('button', { name: category.startsWith('REVENUE') ? 'Adicionar receita' : 'Adicionar saída', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByLabel('Data', { exact: true }).fill('2026-08-10');
    await dialog.getByLabel('Competência', { exact: true }).fill('2026-08');
    await dialog.getByLabel('Descrição', { exact: true }).fill(description);
    await dialog.getByLabel('Valor', { exact: true }).fill(amount);
    await dialog.getByLabel('Categoria', { exact: true }).selectOption(category);
    if (subcategory) await dialog.getByLabel('Subcategoria', { exact: true }).selectOption({ label: subcategory });
    await capture('form-' + category);
    await dialog.getByRole('button', { name: 'Salvar', exact: true }).click();
    await expect(dialog).not.toBeVisible();
    await expect(page.getByRole('cell', { name: description, exact: true })).toBeVisible();
  }
  await page.goto('/');
  await page.bringToFront();
  await expect(page.getByRole('heading', { name: 'Monte sua DRE de forma simples' })).toBeVisible();
  await capture('01-welcome');
  await page.getByRole('button', { name: 'Começar minha DRE' }).click();
  await page.getByLabel('Nome da empresa').fill('Empresa Visual DRE');
  await page.getByLabel('Mês', { exact: true }).selectOption('8');
  await page.getByLabel('Ano', { exact: true }).fill('2026');
  await capture('02-company-period');
  await page.getByRole('button', { name: 'Continuar', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'DRE — Agosto/2026' })).toBeVisible();
  await capture('03-overview-empty');
  await page.getByRole('button', { name: 'Receitas', exact: true }).click();
  await add('Mensalidades', '100000', 'REVENUE_RECURRING');
  await capture('04-revenues');
  await page.getByRole('button', { name: 'Saídas', exact: true }).click();
  await add('Link IP', '20000', 'COST', 'Infraestrutura');
  await capture('05-cost');
  await add('Google Workspace', '1500', 'EXPENSE', 'Tecnologia');
  await capture('06-expense');
  await add('Servidor', '30000', 'INVESTMENT', 'Equipamentos');
  await capture('07-investment');
  await page.getByRole('button', { name: 'Informações Complementares', exact: true }).click();
  await expect(page.getByText('Nenhum ajuste informado.')).toBeVisible();
  await capture('08-adjustments');
  await page.getByRole('button', { name: 'Visão Geral', exact: true }).click();
  await expect(page.locator('.dashboard-results')).toContainText('R$ 78.500,00');
  await capture('09-overview');
  await page.getByRole('button', { name: 'DRE', exact: true }).click();
  for (const [line, value] of Object.entries({ gross_revenue: 'R$ 100.000,00', net_revenue: 'R$ 100.000,00', costs: 'R$ 20.000,00', gross_result: 'R$ 80.000,00', operating_expenses: 'R$ 1.500,00', operating_result: 'R$ 78.500,00', net_result: 'R$ 78.500,00' })) {
    await expect(page.locator(`[data-line="${line}"] .dre-value`)).toHaveText(value);
  }
  for (const [key, value] of Object.entries({ gross: '80,00%', operating: '78,50%', net: '78,50%' })) {
    await expect(page.locator(`[data-margin="${key}"] strong`)).toHaveText(value);
  }
  await expect(page.getByText('Servidor', { exact: true })).toHaveCount(0);
  await capture('10-dre');
  await page.getByRole('button', { name: 'Detalhar Custos', exact: true }).click();
  const panel = page.getByRole('dialog');
  await expect(panel).toContainText('Infraestrutura');
  await expect(panel).toContainText('R$ 20.000,00');
  await expect(panel.getByText('Link IP', { exact: true })).toBeVisible();
  await capture('11-drilldown');
  await panel.getByRole('link', { name: 'Abrir registro de origem' }).click();
  await expect(page.getByRole('cell', { name: 'Servidor', exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('cell', { name: 'Servidor', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Configurações', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Configurações', exact: true })).toBeVisible();
  await capture('12-settings');
  expect(errors).toEqual([]);
});
