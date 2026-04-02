import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,  // 强制串行执行，避免数据冲突
  use: {
    baseURL: 'http://127.0.0.1:3001',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'cd .. && set DATABASE_URL=sqlite+aiosqlite:///./e2e_test.db && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/api/v1/health',
      reuseExistingServer: true,
      timeout: 120000,
    },
    {
      command: 'npm run dev -- --hostname 127.0.0.1 --port 3001',
      url: 'http://127.0.0.1:3001',
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
});
