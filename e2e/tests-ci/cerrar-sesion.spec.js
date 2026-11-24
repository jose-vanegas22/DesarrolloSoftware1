import { test, expect, rutaEvidencia, API } from '../soporte/entorno';

const CORREO = 'autor.jose@prueba.com';
const PASSWORD = 'ClaveSegura123';


// Inicia sesión igual que una persona: llena el formulario, marca el captcha y entra
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

test('E2E-14: cerrar sesión lleva al login y borra los tokens', async ({ page }) => {
  await iniciarSesion(page);

  await page.getByRole('button', { name: 'Cerrar sesión' }).click();

  await expect(page).toHaveURL(/\/login/);
  const access = await page.evaluate(() => localStorage.getItem('access'));
  expect(access).toBeNull();
  await page.screenshot({ path: rutaEvidencia('E2E-14-cerrar-sesion.png') });
});

test('E2E-14 (error): el token viejo ya no sirve después de cerrar sesión', async ({ page }) => {
  await iniciarSesion(page);
  const refresh = await page.evaluate(() => localStorage.getItem('refresh'));

  await page.getByRole('button', { name: 'Cerrar sesión' }).click();
  await expect(page).toHaveURL(/\/login/);

  // Intenta renovar la sesión con el token anterior: el backend debe rechazarlo
  const respuesta = await page.request.post(`${API}/token/refresh/`, { data: { refresh } });
  expect(respuesta.status()).toBe(401);

  // Y si intenta entrar a una página protegida, lo devuelve al login
  await page.goto('/articulos');
  await expect(page).toHaveURL(/\/login/);
  await page.screenshot({ path: rutaEvidencia('E2E-14-sin-acceso.png') });
});
