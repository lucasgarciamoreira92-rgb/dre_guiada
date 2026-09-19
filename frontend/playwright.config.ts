import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:5173", headless: true },
  webServer: [
    {
      command: "../backend/.venv/bin/python ../scripts/e2e_backend.py",
      url: "http://127.0.0.1:8000/openapi.json",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
    },
  ],
});
