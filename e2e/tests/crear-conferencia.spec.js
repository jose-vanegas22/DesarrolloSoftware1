import { test, expect } from '@playwright/test';

// SCRUM-567 | E2E-01: crear conferencia (HU-08).
// Las credenciales se leen solo de variables de entorno: no hay valores por defecto
// y nunca se escriben en el codigo, el reporte ni los mensajes de error.
const CORREO = process.env.E2E_CORREO;
const PASSWORD = process.env.E2E_PASSWORD;

test.describe.configure({ mode: 'default', retries: 0 });
test.use({ trace: 'off', video: 'off', screenshot: 'off' });
test.setTimeout(60000);

// Evita que un artefacto automatico muestre el formulario de login con la contrasena.
// Las unicas capturas son las explicitas, tomadas despues de verificar cada escenario.

function fechaRelativa(dias) {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() + dias);
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${anio}-${mes}-${dia}`;
}

function agregarFicha(testInfo, { historia, pasos, resultado }) {
  testInfo.annotations.push(
    { type: 'Historia', description: historia },
    { type: 'Cuenta', description: 'E2E_CORREO con rol comite' },
    { type: 'Pasos', description: pasos },
    { type: 'Resultado esperado', description: resultado },
  );
}

async function evidencia(page, testInfo, nombre) {
  const captura = await page.screenshot({
    path: `evidencias/${nombre}.png`,
    fullPage: true,
  });
  await testInfo.attach(nombre, { body: captura, contentType: 'image/png' });
}

async function marcarCaptcha(page) {
  const captcha = page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox');

  // El checkbox puede existir mientras el widget sigue cargando; en ese estado
  // aria-disabled=true y la pulsacion se pierde. Esperamos a que este listo.
  await expect(captcha).not.toHaveAttribute('aria-disabled', 'true', { timeout: 15000 });
  await expect(captcha).not.toHaveClass(/recaptcha-checkbox-loading/, { timeout: 15000 });

  await captcha.press('Space');
  await expect(captcha).toBeChecked({ timeout: 15000 });
}

async function iniciarSesionComoComite(page) {
  expect(CORREO, 'Define E2E_CORREO antes de ejecutar la prueba').toBeTruthy();
  expect(PASSWORD, 'Define E2E_PASSWORD antes de ejecutar la prueba').toBeTruthy();

  await page.goto('/login');
  await page.locator('#login-correo').fill(CORREO);
  await page.locator('#login-password').fill(PASSWORD);
  await marcarCaptcha(page);
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();

  // La cuenta tiene autor y comite: el login debe llevar a elegir rol.
  await expect(page).toHaveURL(/\/seleccionar-rol\/?$/, { timeout: 15000 });
  await expect(page.getByRole('heading', { name: '¿Con qué rol quieres ingresar?', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Autor', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Miembro del comité científico', exact: true }).click();

  await expect(page).toHaveURL(/\/inicio\/?$/, { timeout: 15000 });
  await expect(page.locator('.menu-rol')).toHaveText('Comité científico');
}

async function abrirModalCrearConferencia(page) {
  await page.getByRole('link', { name: 'Conferencias', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Conferencias', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Crear conferencia' }).click();

  const modal = page.getByRole('dialog');
  await expect(modal.getByRole('heading', { name: 'Crear conferencia' })).toBeVisible();
  return modal;
}

async function llenarConferencia(modal, { nombre, inicio, fin }) {
  await modal.getByLabel('Nombre').fill(nombre);
  await modal.getByLabel('Fecha de inicio').fill(inicio);
  await modal.getByLabel('Fecha de fin').fill(fin);
}

test.describe('E2E-01 Crear conferencia (HU-08 / SCRUM-567)', () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesionComoComite(page);
  });

  test('E2E-01: crear una conferencia la muestra en la lista', async ({ page }, testInfo) => {
    agregarFicha(testInfo, {
      historia: 'HU-08 (SCRUM-567) — E2E-01: crear conferencia',
      pasos: 'Login con rol comité → Conferencias → Crear conferencia → llenar nombre y fechas → Guardar → filtrar por el nombre',
      resultado: 'Mensaje "Conferencia creada correctamente." y la conferencia visible en la tabla',
    });

    const nombre = `E2E-01 Conferencia ${Date.now()}`;
    const modal = await abrirModalCrearConferencia(page);

    // Fechas pasadas y ordenadas: no abren la postulacion ni estorban a otras pruebas.
    await llenarConferencia(modal, {
      nombre,
      inicio: fechaRelativa(-30),
      fin: fechaRelativa(-20),
    });

    await modal.getByRole('button', { name: 'Guardar conferencia' }).click();
    await expect(modal).toBeHidden();
    await expect(page.getByText('Conferencia creada correctamente.')).toBeVisible();

    await page.getByLabel('Buscar').fill(nombre);
    await page.getByRole('button', { name: 'Filtrar' }).click();
    await expect(page.getByRole('cell', { name: nombre, exact: true })).toBeVisible();
    await expect(page.getByRole('row')).toHaveCount(2); // encabezado + la conferencia filtrada

    await evidencia(page, testInfo, 'E2E-01-crear-conferencia');
  });

  test('E2E-01 (error): rechaza una fecha de fin anterior a la de inicio', async ({ page }, testInfo) => {
    agregarFicha(testInfo, {
      historia: 'HU-08 (SCRUM-567) — E2E-01: crear conferencia, caso de error',
      pasos: 'Login con rol comité → Conferencias → Crear conferencia → fecha de inicio posterior a la de fin → Guardar',
      resultado: 'Error "La fecha de fin no puede ser anterior a la de inicio.", modal abierto y sin mensaje de exito',
    });

    const nombre = `E2E-01 Fecha invalida ${Date.now()}`;
    const modal = await abrirModalCrearConferencia(page);

    await llenarConferencia(modal, {
      nombre,
      inicio: fechaRelativa(-10),
      fin: fechaRelativa(-20),
    });

    await modal.getByRole('button', { name: 'Guardar conferencia' }).click();

    await expect(modal.getByText('La fecha de fin no puede ser anterior a la de inicio.')).toBeVisible();
    await expect(modal).toBeVisible();
    await expect(page.getByText('Conferencia creada correctamente.')).toHaveCount(0);

    await evidencia(page, testInfo, 'E2E-01-fecha-fin-anterior');
  });
});
