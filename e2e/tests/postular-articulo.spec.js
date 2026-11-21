import { test, expect } from '@playwright/test';

// HU-82 (SCRUM-572) / E2E-05 (SCRUM-573): postular un artículo con coautores (HU-10 y HU-11)
const CORREO = process.env.E2E_CORREO ?? 'autor.jose@prueba.com';
const PASSWORD = process.env.E2E_PASSWORD ?? 'ClaveSegura123';

// Un PDF mínimo pero válido: el backend revisa que empiece por %PDF-
const PDF_VALIDO = Buffer.from('%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n');

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

// Abre el formulario desde la lista de conferencias, en la primera que tenga la postulación abierta
async function abrirFormularioPostulacion(page) {
  await page.getByRole('link', { name: 'Conferencias', exact: true }).click();
  await page.getByRole('link', { name: /^Postular artículo a / }).first().click();
  await expect(page.getByRole('heading', { name: 'Postular artículo' })).toBeVisible();
}

// Llena los datos del artículo y del autor responsable
async function llenarDatosArticulo(page, titulo) {
  await page.getByRole('textbox', { name: 'Título' }).fill(titulo);
  await page.getByLabel('Línea temática').selectOption('sistemas_software');
  await page.getByLabel('Resumen').fill('Artículo creado por la prueba E2E-05 para verificar la postulación con coautores.');
  await page.getByRole('textbox', { name: 'Palabras clave' }).fill('pruebas, e2e, playwright');
  await page.locator('#articulo-afiliacion').fill('Universidad del Valle');
}

// Agrega un coautor con el botón "Agregar coautor" y llena su fila
async function agregarCoautor(page, indice, { nombre, afiliacion, correo }) {
  await page.getByRole('button', { name: 'Agregar coautor' }).click();
  await page.locator(`#coautor-nombre-${indice}`).fill(nombre);
  await page.locator(`#coautor-afiliacion-${indice}`).fill(afiliacion);
  await page.locator(`#coautor-correo-${indice}`).fill(correo);
}

// Guarda la captura en evidencias/ y la adjunta al reporte de Playwright
async function evidencia(page, testInfo, nombre) {
  const captura = await page.screenshot({ path: `evidencias/${nombre}.png`, fullPage: true });
  await testInfo.attach(nombre, { body: captura, contentType: 'image/png' });
}

test.describe('E2E-05 Postular artículo con coautores (HU-10 y HU-11)', () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page);
  });

  test('E2E-05: el artículo queda Postulado con sus coautores', async ({ page }, testInfo) => {
    testInfo.annotations.push(
      { type: 'Historia', description: 'HU-82 (SCRUM-572) — subtarea E2E-05 (SCRUM-573), cubre HU-10 y HU-11' },
      { type: 'Pasos', description: 'Iniciar sesión como autor → Conferencias → Postular artículo → llenar datos → agregar 2 coautores → adjuntar PDF → Postular → abrir el detalle' },
      { type: 'Resultado esperado', description: 'Mensaje "Artículo postulado correctamente.", estado Postulado y los dos coautores en el detalle' },
    );
    const titulo = `E2E-05 Artículo con coautores ${Date.now()}`;
    const coautores = [
      { nombre: 'Laura Gómez', afiliacion: 'Universidad del Valle', correo: `laura.${Date.now()}@prueba.com` },
      { nombre: 'Andrés Ruiz', afiliacion: 'Universidad Icesi', correo: `andres.${Date.now()}@prueba.com` },
    ];

    await abrirFormularioPostulacion(page);
    await llenarDatosArticulo(page, titulo);
    await agregarCoautor(page, 0, coautores[0]);
    await agregarCoautor(page, 1, coautores[1]);
    await page.locator('#articulo-pdf').setInputFiles({ name: 'articulo-e2e-05.pdf', mimeType: 'application/pdf', buffer: PDF_VALIDO });
    await evidencia(page, testInfo, 'E2E-05-formulario');
    await page.getByRole('button', { name: 'Postular artículo' }).click();

    // Vuelve a Conferencias con el mensaje de éxito
    await expect(page).toHaveURL(/\/conferencias/);
    await expect(page.getByText('Artículo postulado correctamente.')).toBeVisible();

    // En el detalle el artículo aparece Postulado, con el autor responsable y los dos coautores
    await page.getByRole('link', { name: 'Artículos', exact: true }).click();
    await page.getByRole('link', { name: `Ver detalle de ${titulo}` }).click();
    await expect(page.getByRole('heading', { name: titulo })).toBeVisible();
    await expect(page.locator('.detalle-encabezado .detalle-etiqueta')).toHaveText('Postulado');
    const autores = page.locator('.detalle-autores li');
    await expect(autores).toHaveCount(3);
    for (const coautor of coautores) {
      await expect(autores.filter({ hasText: coautor.nombre })).toContainText(coautor.correo);
    }
    await evidencia(page, testInfo, 'E2E-05-postulado');
  });

  test('E2E-05 (error): se rechaza un coautor con el correo repetido', async ({ page }, testInfo) => {
    testInfo.annotations.push(
      { type: 'Historia', description: 'HU-82 (SCRUM-572) — subtarea E2E-05 (SCRUM-573)' },
      { type: 'Pasos', description: 'Postular con un coautor que usa el mismo correo del autor responsable' },
      { type: 'Resultado esperado', description: 'Error "No puedes repetir el correo de un autor." y el artículo no se crea' },
    );
    const titulo = `E2E-05 Correo repetido ${Date.now()}`;

    await abrirFormularioPostulacion(page);
    await llenarDatosArticulo(page, titulo);
    await agregarCoautor(page, 0, { nombre: 'Coautor Repetido', afiliacion: 'Universidad del Valle', correo: CORREO });
    await page.locator('#articulo-pdf').setInputFiles({ name: 'articulo-e2e-05.pdf', mimeType: 'application/pdf', buffer: PDF_VALIDO });
    await page.getByRole('button', { name: 'Postular artículo' }).click();

    // El backend responde con el error y el formulario no avanza
    await expect(page.getByText('No puedes repetir el correo de un autor.')).toBeVisible();
    await expect(page).toHaveURL(/\/articulos\/postular/);
    await expect(page.getByText('El artículo quedó registrado')).toHaveCount(0);
    await evidencia(page, testInfo, 'E2E-05-correo-repetido');

    // Y el artículo no aparece en la lista
    await page.getByRole('link', { name: 'Artículos', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Artículos' })).toBeVisible();
    await expect(page.getByRole('link', { name: `Ver detalle de ${titulo}` })).toHaveCount(0);
  });
});
