import { test, expect } from '@playwright/test';

const CORREO_LOGIN = "autor.valencia@prueba1.com";
const PASSWORD_LOGIN = "@Valencia1";
const CORREO_BLOQUEO = "autor.valencia@prueba2.com";
const PASSWORD_INCORRECTA = "contraseña_equivocada";
// Credencial de una cuenta exclusiva de pruebas, compartida para ejecutar este caso.
const PASSWORD_BLOQUEO = '@Valencia2';

// Evita reintentos automaticos: repetir el caso de bloqueo altera sus precondiciones.
test.describe.configure({ mode: 'default', retries: 0 });
test.use({ screenshot: 'only-on-failure' });
test.setTimeout(60000);

async function enviarLogin(page, correo, password) {
  await page.locator('#login-correo').fill(correo);
  await page.locator('#login-password').fill(password);
  // El titulo del iframe es estable; su nombre generado cambia en cada carga.
  const captcha = page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox');
  await expect(captcha).not.toBeChecked();
  await captcha.press('Space');
  await expect(captcha).toBeChecked();

  // Espera la respuesta de ESTE intento, sin confundirla con un error anterior.
  const [respuesta] = await Promise.all([
    page.waitForResponse((respuesta) =>
      new URL(respuesta.url()).pathname === '/api/token/' &&
      respuesta.request().method() === 'POST'),
    page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click(),
  ]);
  return respuesta;
}

test('E2E-03: iniciar sesión con reCAPTCHA', async ({ page }) => {
  await page.goto('/login');
  const respuesta = await enviarLogin(page, CORREO_LOGIN, PASSWORD_LOGIN);
  expect(respuesta.status()).toBe(200);
  // Esta cuenta debe tener un solo rol para entrar directamente a Inicio.
  await expect(page).toHaveURL(/\/inicio\/?$/);
  await expect(page.getByRole('link', { name: 'Mi perfil', exact: true })).toBeVisible();
  await page.screenshot({ path: 'evidencias/E2E-03-login-exito.png', fullPage: true });
});

test('E2E-03 (error): cinco fallos bloquean incluso la contraseña correcta', async ({ page }) => {
  test.setTimeout(180000);
  expect(PASSWORD_INCORRECTA).not.toBe(PASSWORD_BLOQUEO);

  // Un acceso correcto verifica la cuenta y deja su contador de fallos en cero.
  // Si sigue bloqueada por una ejecucion anterior, espera los 15 minutos antes de repetir.
  await page.goto('/login');
  const acceso = await enviarLogin(page, CORREO_BLOQUEO, PASSWORD_BLOQUEO);
  expect(acceso.status(), 'La cuenta debe estar activa y desbloqueada, con la contraseña correcta.').toBe(200);
  await expect(page).toHaveURL(/\/inicio\/?$/);
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
  await expect(page).toHaveURL(/\/login\/?$/);

  for (let intento = 1; intento <= 5; intento += 1) {
    await test.step(`Intento incorrecto ${intento} de 5`, async () => {
      const respuesta = await enviarLogin(page, CORREO_BLOQUEO, PASSWORD_INCORRECTA);
      expect(respuesta.status()).toBe(401);
      const datos = await respuesta.json();
      expect(typeof datos.detail).toBe('string');
      expect(datos.detail.length).toBeGreaterThan(0);
      expect(datos.detail).not.toMatch(/Cuenta bloqueada/i);
      await expect(page.locator('.acceso-formulario .mensaje-error')).toHaveText(datos.detail);
      await expect(page).toHaveURL(/\/login\/?$/);
      // El formulario reinicia el CAPTCHA tras cada error; no reutilizamos el token.
      await expect(page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox')).not.toBeChecked();
    });
  }

  // El quinto fallo activa el bloqueo; el siguiente envio muestra el mensaje especifico.
  const bloqueada = await enviarLogin(page, CORREO_BLOQUEO, PASSWORD_BLOQUEO);
  expect(bloqueada.status()).toBe(401);
  const datos = await bloqueada.json();
  expect(datos.detail).toMatch(/Cuenta bloqueada por demasiados intentos fallidos/);
  await expect(page.locator('.acceso-formulario .mensaje-error')).toContainText('Cuenta bloqueada por demasiados intentos fallidos');
  await expect(page).toHaveURL(/\/login\/?$/);
  expect(await page.evaluate(() => localStorage.getItem('access'))).toBeNull();
  await page.screenshot({ path: 'evidencias/E2E-03-bloqueo.png', fullPage: true });
});
