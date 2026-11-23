import { test, expect, rutaEvidencia, aislado } from '../soporte/entorno';

const CORREO = "autor.valencia@prueba2.2.com";
const PASSWORD = "@Valencia3";

if (!aislado) test.describe.configure({ mode: 'default', retries: 0 });
test.use({ screenshot: 'only-on-failure' });
test.setTimeout(60000);

async function abrirSeleccionDeRol(page) {
  await page.goto('/login');
  await page.locator('#login-correo').fill(CORREO);
  await page.locator('#login-password').fill(PASSWORD);
  const captcha = page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox');
  await captcha.press('Space');
  await expect(captcha).toBeChecked();
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  // El usuario grabado tiene autor y comite: no debe saltarse esta pantalla.
  await expect(page).toHaveURL(/\/seleccionar-rol\/?$/);
  await expect(page.getByRole('heading', { name: '¿Con qué rol quieres ingresar?', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Autor', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Miembro del comité científico', exact: true })).toBeVisible();
}

test('E2E-04: un usuario con varios roles elige comité', async ({ page }) => {
  await abrirSeleccionDeRol(page);
  await page.getByRole('button', { name: 'Miembro del comité científico', exact: true }).click();
  await expect(page).toHaveURL(/\/inicio\/?$/);
  await expect(page.locator('.menu-rol')).toHaveText('Comité científico');
  await expect(page.getByRole('link', { name: 'Usuarios', exact: true })).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem('rol_activo'))).toBe('comite');
  await page.screenshot({ path: rutaEvidencia('E2E-04-rol-comite.png'), fullPage: true });
});

test('E2E-04 (error): no se ofrece el rol administrador a quien no lo tiene', async ({ page }) => {
  await abrirSeleccionDeRol(page);
  // Comprobamos la ausencia solo despues de verificar que la pantalla ya cargo.
  await expect(page.getByRole('button', { name: 'Administrador del sistema', exact: true })).toHaveCount(0);
  await page.screenshot({ path: rutaEvidencia('E2E-04-rol-no-disponible.png'), fullPage: true });
});
