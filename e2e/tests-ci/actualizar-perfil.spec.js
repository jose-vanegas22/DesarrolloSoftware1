import { test, expect, rutaEvidencia } from '../soporte/entorno';

const CORREO = 'autor.miguel@prueba.com';
const PASSWORD = 'ClaveSegura123';

async function iniciarSesion(page) {
  await page.goto('/login');
  await page.locator('#login-correo').fill(CORREO);
  await page.locator('#login-password').fill(PASSWORD);
  const captcha = page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox');
  await captcha.press('Space');
  await expect(captcha).toBeChecked();
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await expect(page).toHaveURL(/\/inicio/);
}

test('E2E-08: actualiza apellidos y teléfono del perfil', async ({ page }) => {
  await iniciarSesion(page);
  await page.getByRole('link', { name: 'Mi perfil' }).click();

  const telefono = `31${Date.now().toString().slice(-8)}`; // Distinto en cada corrida
  await page.getByRole('textbox', { name: 'Apellidos' }).fill('Cruz Rincon');
  await page.getByRole('textbox', { name: 'Teléfono' }).fill(telefono);
  await page.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(page.getByText('Perfil actualizado correctamente.')).toBeVisible();

  // Al recargar, los datos vienen del backend: asi se comprueba que se guardaron
  await page.reload();
  await expect(page.getByRole('textbox', { name: 'Apellidos' })).toHaveValue('Cruz Rincon');
  await expect(page.getByRole('textbox', { name: 'Teléfono' })).toHaveValue(telefono);
  await page.screenshot({ path: rutaEvidencia('E2E-08-perfil.png') });
});

test('E2E-08 (error): no guarda con un campo obligatorio vacío', async ({ page }) => {
  await iniciarSesion(page);
  await page.getByRole('link', { name: 'Mi perfil' }).click();

  const apellidos = page.getByRole('textbox', { name: 'Apellidos' });
  await apellidos.fill('');
  await page.getByRole('button', { name: 'Guardar cambios' }).click();

  expect(await apellidos.evaluate((campo) => campo.validity.valueMissing)).toBe(true);
  await expect(page.getByText('Perfil actualizado correctamente.')).toHaveCount(0);
  await page.screenshot({ path: rutaEvidencia('E2E-08-campo-vacio.png') });
});
