import { defineConfig } from '@playwright/test';
import base from './playwright.config';

export default defineConfig({
  ...base,
  testDir: './visual',
  timeout: 180_000,
  retries: 0,
  outputDir: process.env.DRE_VISUAL_DIR + '/artifacts',
  reporter: [['list'], ['json', { outputFile: process.env.DRE_VISUAL_DIR + '/playwright.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    browserName: 'chromium',
    headless: false,
    viewport: { width: 1440, height: 900 },
    launchOptions: { slowMo: 250 },
    video: { mode: 'on', size: { width: 1440, height: 900 } },
    trace: 'on',
  },
});
