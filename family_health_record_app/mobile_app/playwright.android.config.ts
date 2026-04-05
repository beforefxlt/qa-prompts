import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: 'http://10.0.2.2:3001',
    trace: 'on-first-retry',
    permissions: ['geolocation'],
  },
  projects: [
    {
      name: 'Android Emulator',
      use: {
        ...devices['Pixel 7'],
        appium: {
          platformName: 'Android',
          deviceName: 'Android Emulator',
          appWaitActivity: '*',
        },
      },
    },
  ],
});