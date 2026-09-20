import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

test.use({ viewport: { width: 1440, height: 900 } });

test('capture eight stable milestone screens', async ({ page, request }) => {
  const directory = process.env.DRE_SCREENSHOT_DIR || resolve('../validation-results/screenshots/manual');
  await mkdir(directory, { recursive: true });
  async function capture(name: string) {
    await expect(page.getByText(/Carregando/)).toHaveCount(0);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: resolve(directory, name + '.png'), animations: 'disabled', fullPage: true });
  }
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Começar minha DRE' })).toBeVisible();
  await capture('01-welcome');
  await page.getByRole('button', { name: 'Começar minha DRE' }).click();
  await page.getByLabel('Nome da empresa').fill('Empresa Teste DRE');
  await page.getByLabel('Mês', { exact: true }).selectOption('8');
  await page.getByLabel('Ano', { exact: true }).fill('2026');
  await capture('02-company-period');
  await page.getByRole('button', { name: 'Continuar', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'DRE — Agosto/2026' })).toBeVisible();
  const id = new URL(page.url()).searchParams.get('period');
  for (const values of [
    { direction: 'IN', description: 'Mensalidades', amount: '100000', main_category: 'REVENUE_RECURRING' },
    { direction: 'OUT', description: 'Link IP', amount: '20000', main_category: 'COST' },
    { direction: 'OUT', description: 'Google Workspace', amount: '1500', main_category: 'EXPENSE' },
    { direction: 'OUT', description: 'Servidor', amount: '30000', main_category: 'INVESTMENT' },
  ]) {
    const response = await request.post(`/api/periods/${id}/transactions`, { data: {
      transaction_date: '2026-08-10', competence_month: 8, competence_year: 2026, ...values,
    } });
    expect(response.status()).toBe(201);
  }
  await page.reload();
  await expect(page.locator('.dashboard-results')).toContainText('R$ 78.500,00');
  await expect(page.getByRole('progressbar', { name: 'Receitas' })).toHaveAttribute('aria-valuenow', '100');
  await expect(page.getByRole('progressbar', { name: 'Saídas' })).toHaveAttribute('aria-valuenow', '100');
  await capture('03-overview');
  await page.getByRole('button', { name: 'Receitas', exact: true }).click();
  await expect(page.getByRole('cell', { name: 'Mensalidades', exact: true })).toBeVisible();
  await capture('04-revenues');
  await page.getByRole('button', { name: 'Saídas', exact: true }).click();
  await expect(page.getByRole('cell', { name: 'Servidor', exact: true })).toBeVisible();
  await capture('05-expenses');
  await page.getByRole('button', { name: 'Informações Complementares', exact: true }).click();
  await expect(page.getByText('Nenhum ajuste informado.')).toBeVisible();
  await capture('06-adjustments');
  await page.getByRole('button', { name: 'DRE', exact: true }).click();
  await expect(page.locator('[data-line="net_result"] .dre-value')).toHaveText('R$ 78.500,00');
  await capture('07-dre');
  await page.getByRole('button', { name: 'Configurações', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Configurações', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Equipamentos', exact: true })).toBeVisible();
  await capture('08-settings');
});
