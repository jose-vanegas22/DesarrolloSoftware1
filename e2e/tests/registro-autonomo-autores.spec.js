import { test, expect } from '@playwright/test';

async function marcarCaptcha(page) {
  const captcha = page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox');
  await captcha.press('Space');
  await expect(captcha).toBeChecked();
}

async function llenarRegistro(page, correo) {
  await page.goto('/registro');
  await page.getByRole('textbox', { name: 'Nombres' }).fill('Aurora');
  await page.getByRole('textbox', { name: 'Apellidos' }).fill('Cruz Giron');
  await page.getByRole('textbox', { name: 'Correo electrónico' }).fill(correo);
  await page.getByRole('textbox', { name: 'Teléfono (opcional)' }).fill('3187598640');
  await page.getByRole('textbox', { name: 'Contraseña', exact: true }).fill('ClaveSegura123');
  await page.getByRole('textbox', { name: 'Confirmar contraseña' }).fill('ClaveSegura123');
  await marcarCaptcha(page);
  await page.getByRole('button', { name: 'Crear cuenta' }).click();
}

test('E2E-07: registra un autor nuevo y lo lleva al inicio de sesión', async ({ page }) => {
  await llenarRegistro(page, `aurora.${Date.now()}@example.com`);

  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByText('Cuenta creada. Ya puedes iniciar sesión.')).toBeVisible();
  await page.screenshot({ path: 'evidencias/E2E-07-registro.png' });
});

test('E2E-07 (error): rechaza un correo ya registrado', async ({ page }) => {
  await llenarRegistro(page, 'autor.miguel@prueba.com'); // Cuenta de prueba que ya existe

  await expect(page.getByText(/Ya existe/)).toBeVisible();
  await expect(page).toHaveURL(/\/registro/);
  await page.screenshot({ path: 'evidencias/E2E-07-correo-repetido.png' });
});