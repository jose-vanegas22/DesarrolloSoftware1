// Configuracion exclusiva de las copias adaptadas al entorno aislado.
import path from 'node:path';
import { defineConfig } from '@playwright/test';
import configuracionEquipo from './playwright.config';

// Tambien al ejecutarla localmente exige la base y los servidores E2E.
process.env.E2E_AISLADO = '1';

export default defineConfig(configuracionEquipo, {
  testDir: './tests-ci',
  fullyParallel: false,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/resultados.json' }],
  ],
  use: { screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  webServer: [
    {
      name: 'Backend E2E',
      command: 'node soporte/servidor-backend.cjs',
      cwd: __dirname,
      url: 'http://127.0.0.1:8000/api/e2e/entorno/',
      reuseExistingServer: false,
      timeout: 60000,
      gracefulShutdown: { signal: 'SIGTERM', timeout: 5000 },
    },
    {
      name: 'Frontend E2E',
      command: 'npm run build && npm run preview -- --host localhost --port 5173 --strictPort',
      cwd: path.resolve(__dirname, '../frontend'),
      url: 'http://localhost:5173/login',
      env: {
        VITE_API_URL: 'http://127.0.0.1:8000/api',
        VITE_RECAPTCHA_SITE_KEY: '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI',
      },
      reuseExistingServer: false,
      timeout: 60000,
      gracefulShutdown: { signal: 'SIGTERM', timeout: 5000 },
    },
  ],
});
