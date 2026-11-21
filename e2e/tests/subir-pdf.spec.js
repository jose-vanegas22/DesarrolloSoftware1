import { test, expect } from '@playwright/test';

// HU-82 (SCRUM-572) / E2E-06 (SCRUM-574): subir el PDF del artículo (HU-68)
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

// Abre el formulario de postulación y llena los datos obligatorios del artículo
async function prepararPostulacion(page, titulo) {
  await page.getByRole('link', { name: 'Conferencias', exact: true }).click();
  await page.getByRole('link', { name: /^Postular artículo a / }).first().click();
  await expect(page.getByRole('heading', { name: 'Postular artículo' })).toBeVisible();
  await page.getByRole('textbox', { name: 'Título' }).fill(titulo);
  await page.getByLabel('Línea temática').selectOption('tecnologias_informatica');
  await page.getByLabel('Resumen').fill('Artículo creado por la prueba E2E-06 para verificar la subida del PDF.');
  await page.getByRole('textbox', { name: 'Palabras clave' }).fill('pdf, e2e, playwright');
  await page.locator('#articulo-afiliacion').fill('Universidad del Valle');
}

// Guarda la captura en evidencias/ y la adjunta al reporte de Playwright
async function evidencia(page, testInfo, nombre) {
  const captura = await page.screenshot({ path: `evidencias/${nombre}.png`, fullPage: true });
  await testInfo.attach(nombre, { body: captura, contentType: 'image/png' });
}

test.describe('E2E-06 Subir el PDF del artículo (HU-68)', () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page);
  });

  test('E2E-06: el PDF se sube y aparece la fecha de entrega', async ({ page }, testInfo) => {
    testInfo.annotations.push(
      { type: 'Historia', description: 'HU-82 (SCRUM-572) — subtarea E2E-06 (SCRUM-574), cubre HU-68' },
      { type: 'Pasos', description: 'Postular un artículo con un PDF válido y abrir su detalle' },
      { type: 'Resultado esperado', description: 'El detalle muestra "Entregado el …" en la tarjeta Artículo en PDF' },
    );
    const titulo = `E2E-06 PDF entregado ${Date.now()}`;

    await prepararPostulacion(page, titulo);
    await page.locator('#articulo-pdf').setInputFiles({ name: 'articulo-e2e-06.pdf', mimeType: 'application/pdf', buffer: PDF_VALIDO });
    await page.getByRole('button', { name: 'Postular artículo' }).click();
    await expect(page.getByText('Artículo postulado correctamente.')).toBeVisible();

    await page.getByRole('link', { name: 'Artículos', exact: true }).click();
    await page.getByRole('link', { name: `Ver detalle de ${titulo}` }).click();
    await expect(page.getByRole('heading', { name: titulo })).toBeVisible();
    await expect(page.getByText(/^Entregado el /)).toBeVisible();
    await expect(page.getByText('Todavía no se ha entregado el PDF.')).toHaveCount(0);
    await evidencia(page, testInfo, 'E2E-06-pdf-entregado');
  });

  test('E2E-06 (error): se rechaza un archivo que no es PDF', async ({ page }, testInfo) => {
    testInfo.annotations.push(
      { type: 'Historia', description: 'HU-82 (SCRUM-572) — subtarea E2E-06 (SCRUM-574)' },
      { type: 'Pasos', description: 'Postular adjuntando un archivo de texto; después corregirlo con un PDF válido' },
      { type: 'Resultado esperado', description: 'Error "Solo se permiten archivos PDF." sin fecha de entrega; con el PDF correcto la postulación termina' },
    );
    const titulo = `E2E-06 Archivo no PDF ${Date.now()}`;

    await prepararPostulacion(page, titulo);
    await page.locator('#articulo-pdf').setInputFiles({ name: 'notas.txt', mimeType: 'text/plain', buffer: Buffer.from('Esto no es un PDF') });
    await page.getByRole('button', { name: 'Postular artículo' }).click();

    // El backend rechaza el archivo: el artículo queda registrado pero sin PDF
    await expect(page.getByText('Solo se permiten archivos PDF.')).toBeVisible();
    await expect(page.getByText('El artículo quedó registrado. Solo falta subir el PDF.')).toBeVisible();
    await expect(page).toHaveURL(/\/articulos\/postular/);
    await evidencia(page, testInfo, 'E2E-06-no-es-pdf');

    // Con un PDF válido el autor termina la postulación sin repetir los datos
    await page.locator('#articulo-pdf').setInputFiles({ name: 'articulo-e2e-06.pdf', mimeType: 'application/pdf', buffer: PDF_VALIDO });
    await page.getByRole('button', { name: 'Postular artículo' }).click();
    await expect(page.getByText('Artículo postulado correctamente.')).toBeVisible();
  });

  test('E2E-06 (error): se rechaza un PDF de más de 10 MB', async ({ page }, testInfo) => {
    testInfo.annotations.push(
      { type: 'Historia', description: 'HU-82 (SCRUM-572) — subtarea E2E-06 (SCRUM-574)' },
      { type: 'Pasos', description: 'Postular adjuntando un PDF de 11 MB' },
      { type: 'Resultado esperado', description: 'Error "El PDF no puede superar 10 MB." y no se registra el artículo' },
    );
    const titulo = `E2E-06 PDF muy grande ${Date.now()}`;
    const pdfGrande = Buffer.concat([PDF_VALIDO, Buffer.alloc(11 * 1024 * 1024, ' ')]);

    await prepararPostulacion(page, titulo);
    await page.locator('#articulo-pdf').setInputFiles({ name: 'articulo-grande.pdf', mimeType: 'application/pdf', buffer: pdfGrande });
    await page.getByRole('button', { name: 'Postular artículo' }).click();

    await expect(page.getByText('El PDF no puede superar 10 MB.')).toBeVisible();
    await expect(page.getByText('El artículo quedó registrado')).toHaveCount(0);
    await evidencia(page, testInfo, 'E2E-06-pdf-grande');

    // El artículo no se creó
    await page.getByRole('link', { name: 'Artículos', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Artículos' })).toBeVisible();
    await expect(page.getByRole('link', { name: `Ver detalle de ${titulo}` })).toHaveCount(0);
  });
});
