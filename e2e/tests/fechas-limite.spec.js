import { test, expect } from '@playwright/test';

// SCRUM-568 | E2E-02: configurar fechas límite (HU-09).
// Las credenciales se leen solo de variables de entorno: no hay valores por defecto
// y nunca se escriben en el codigo, el reporte ni los mensajes de error.
const CORREO = process.env.E2E_CORREO;
const PASSWORD = process.env.E2E_PASSWORD;

const ETIQUETAS = {
  postulacion: 'Postulación',
  revision: 'Revisión',
  version_corregida: 'Versión corregida',
  version_final: 'Versión final',
};

test.describe.configure({ mode: 'default', retries: 0 });
test.use({ trace: 'off', video: 'off', screenshot: 'off' });
test.setTimeout(90000);

function fechaSoloRelativa(dias) {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() + dias);
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${anio}-${mes}-${dia}`;
}

// Mediodia para evitar desfases de dia al serializar en America/Bogota.
function fechaHoraRelativa(dias) {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() + dias);
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${anio}-${mes}-${dia}T12:00`;
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

// Cada prueba crea su propia conferencia: no depende de E2E-01 ni de orden de ejecucion.
async function crearConferencia(page, nombre) {
  await page.getByRole('link', { name: 'Conferencias', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Conferencias', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Crear conferencia' }).click();

  const modal = page.getByRole('dialog');
  await modal.getByLabel('Nombre').fill(nombre);
  await modal.getByLabel('Fecha de inicio').fill(fechaSoloRelativa(-40));
  await modal.getByLabel('Fecha de fin').fill(fechaSoloRelativa(-10));
  await modal.getByRole('button', { name: 'Guardar conferencia' }).click();

  await expect(modal).toBeHidden();
  await expect(page.getByText('Conferencia creada correctamente.')).toBeVisible();
}

async function abrirFechasLimite(page, nombre) {
  await page.getByRole('button', { name: `Fechas límite de ${nombre}` }).click();

  const modal = page.getByRole('dialog');
  await expect(modal.getByRole('heading', { name: 'Fechas límite' })).toBeVisible();
  await expect(modal.getByText(nombre)).toBeVisible();
  return modal;
}

async function llenarFechas(modal, fechas) {
  for (const [campo, etiqueta] of Object.entries(ETIQUETAS)) {
    await modal.getByLabel(etiqueta).fill(fechas[campo]);
  }
}

test.describe('E2E-02 Configurar fechas límite (HU-09 / SCRUM-568)', () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesionComoComite(page);
  });

  test('E2E-02: guardar y conservar las fechas de cada etapa', async ({ page }, testInfo) => {
    agregarFicha(testInfo, {
      historia: 'HU-09 (SCRUM-568) — E2E-02: configurar fechas límite',
      pasos: 'Login con rol comité → crear conferencia → Fechas límite → llenar cuatro etapas → Guardar → reabrir el modal',
      resultado: 'Mensaje "Fechas límite guardadas correctamente." y las cuatro fechas conservadas al reabrir',
    });

    const nombre = `E2E-02 Conferencia ${Date.now()}`;
    await crearConferencia(page, nombre);

    // Fechas pasadas y ordenadas: no abren la postulacion ni estorban a otras pruebas.
    const fechas = {
      postulacion: fechaHoraRelativa(-40),
      revision: fechaHoraRelativa(-30),
      version_corregida: fechaHoraRelativa(-20),
      version_final: fechaHoraRelativa(-10),
    };

    const modal = await abrirFechasLimite(page, nombre);
    await expect(modal.getByLabel('Postulación')).toBeEnabled();
    await llenarFechas(modal, fechas);
    await modal.getByRole('button', { name: 'Guardar fechas' }).click();

    await expect(modal).toBeHidden();
    await expect(page.getByText('Fechas límite guardadas correctamente.')).toBeVisible();
    await evidencia(page, testInfo, 'E2E-02-fechas-guardadas');

    // Reabrir comprueba que el GET devolvio y el formulario conservo cada etapa.
    const reabierto = await abrirFechasLimite(page, nombre);
    await expect(reabierto.getByLabel('Postulación')).toBeEnabled();
    for (const [campo, etiqueta] of Object.entries(ETIQUETAS)) {
      await expect(reabierto.getByLabel(etiqueta)).toHaveValue(fechas[campo]);
    }
    await evidencia(page, testInfo, 'E2E-02-fechas-reabiertas');
  });

  test('E2E-02 (error): rechaza fechas fuera de orden', async ({ page }, testInfo) => {
    agregarFicha(testInfo, {
      historia: 'HU-09 (SCRUM-568) — E2E-02: configurar fechas límite, caso de error',
      pasos: 'Login con rol comité → crear conferencia → Fechas límite → Revisión anterior a Postulación → Guardar',
      resultado: 'Error "Debe ser posterior a Postulación.", modal abierto y sin mensaje de exito',
    });

    const nombre = `E2E-02 Fechas desordenadas ${Date.now()}`;
    await crearConferencia(page, nombre);

    const modal = await abrirFechasLimite(page, nombre);
    await expect(modal.getByLabel('Postulación')).toBeEnabled();
    await llenarFechas(modal, {
      postulacion: fechaHoraRelativa(-30),
      revision: fechaHoraRelativa(-40),
      version_corregida: fechaHoraRelativa(-20),
      version_final: fechaHoraRelativa(-10),
    });

    await modal.getByRole('button', { name: 'Guardar fechas' }).click();

    await expect(modal.getByText('Debe ser posterior a Postulación.')).toBeVisible();
    await expect(modal).toBeVisible();
    await expect(page.getByText('Fechas límite guardadas correctamente.')).toHaveCount(0);

    await evidencia(page, testInfo, 'E2E-02-fechas-desordenadas');
  });
});
