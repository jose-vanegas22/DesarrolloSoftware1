import { test, expect } from '@playwright/test';

// Ejecutar desde e2e: E2E_AUTOR_PASSWORD='[CONTRASEÑA]' E2E_COMITE_PASSWORD='[MISMA-CONTRASEÑA]' npx playwright test tests/consultar-articulos.spec.js --headed

// No graba credenciales en trazas ni videos.
test.use({ trace: 'off', video: 'off' });

test('E2E-11: autor filtra sus artículos por título y limpia el filtro', async ({ page }) => {
  // Lee la contraseña del autor.
  const password = process.env.E2E_AUTOR_PASSWORD;
  expect(password, 'Define E2E_AUTOR_PASSWORD antes de ejecutar la prueba').toBeTruthy();

  // login
  await page.goto('http://localhost:5173/login');
  // llena correo
  await page.getByRole('textbox', { name: 'Correo electrónico' }).click();
  await page.getByRole('textbox', { name: 'Correo electrónico' }).fill('juandavid@teste2e.com');
  // Llena la contraseña
  await page.getByRole('textbox', { name: 'Contraseña' }).click();
  await page.getByRole('textbox', { name: 'Contraseña' }).fill(password);
  // captcha
  const captcha = page
    .frameLocator('iframe[title="reCAPTCHA"]')
    .getByRole('checkbox');
  await captcha.press('Space');
  await expect(captcha).toBeChecked();

  // Inicia sesión
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  // Abre Artículos y define los títulos a comprobar.
  await page.getByRole('link', { name: 'Artículos' }).click();
  const buscado = page.getByRole('cell', { name: 'articulo2', exact: true });
  const excluido = page.getByRole('cell', { name: 'estamos melos', exact: true });
  // Escribe el título
  await page.getByRole('textbox', { name: 'Título' }).click();
  await page.getByRole('textbox', { name: 'Título' }).fill('articulo2');
  // Aplica el filtro.
  await page.getByRole('button', { name: 'Filtrar' }).click();

  // Comprueba qué artículo aparece y cuál no.
  await expect(excluido).toHaveCount(0);
  await expect(buscado).toBeVisible();

  // Captura el filtrado.
  await page.screenshot({ path: 'evidencias/E2E-11-autor-filtrado.png', fullPage: true });

  // Limpia el filtro.
  await page.getByRole('button', { name: 'Limpiar' }).click();

  // Comprueba el campo vacío y los dos artículos.
  await expect(page.getByRole('textbox', { name: 'Título' })).toHaveValue('');
  await expect(buscado).toBeVisible();
  await expect(excluido).toBeVisible();

  // Captura el listado sin filtro.
  await page.screenshot({ path: 'evidencias/E2E-11-autor-limpiar.png', fullPage: true });
});


test('E2E-11: comité filtra artículos por título, autor, conferencia y estado', async ({ page }) => {
  // Lee la contraseña del comité.
  const password = process.env.E2E_COMITE_PASSWORD;
  expect(password, 'Define E2E_COMITE_PASSWORD antes de ejecutar la prueba').toBeTruthy();

  // Abre el login.
  await page.goto('http://localhost:5173/login');

  // Llena el correo del comité.
  await page.getByRole('textbox', { name: 'Correo electrónico' }).click();
  await page.getByRole('textbox', { name: 'Correo electrónico' }).fill('juan.salazar.caicedo@correunivalle.edu.co');

  // Llena la contraseña.
  await page.getByRole('textbox', { name: 'Contraseña' }).click();
  await page.getByRole('textbox', { name: 'Contraseña' }).fill(password);

  // Marca el captcha.
  const captcha = page
    .frameLocator('iframe[title="reCAPTCHA"]')
    .getByRole('checkbox');
  await captcha.press('Space');
  await expect(captcha).toBeChecked();

  // Inicia sesión y abre Artículos.
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  await page.getByRole('link', { name: 'Artículos' }).click();
  const articulo2 = page.getByRole('cell', { name: 'articulo2', exact: true });
  const estamosMelos = page.getByRole('cell', { name: 'estamos melos', exact: true });

  // Filtra por una palabra común.
  await page.getByRole('textbox', { name: 'Título' }).click();
  await page.getByRole('textbox', { name: 'Título' }).fill('articulo');
  await page.getByRole('button', { name: 'Filtrar' }).click();

  // Comprueba los títulos que contienen la palabra.
  await expect(estamosMelos).toHaveCount(0);
  await expect(articulo2).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Articulo 1', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Articulo sobre IA de prueba', exact: true })).toBeVisible();
  await expect(page.locator('tbody tr td:first-child').filter({ hasNotText: /articulo/i })).toHaveCount(0);
  await page.screenshot({ path: 'evidencias/E2E-11-comite-palabra.png', fullPage: true });

  // Filtra por un título específico.
  await page.getByRole('textbox', { name: 'Título' }).click();
  await page.getByRole('textbox', { name: 'Título' }).fill('articulo2');
  await page.getByRole('button', { name: 'Filtrar' }).click();
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await expect(articulo2).toBeVisible();
  await expect(estamosMelos).toHaveCount(0);
  await page.screenshot({ path: 'evidencias/E2E-11-comite-titulo.png', fullPage: true });

  // Limpia el título.
  await page.getByRole('button', { name: 'Limpiar' }).click();
  await expect(page.getByRole('textbox', { name: 'Título' })).toHaveValue('');

  // Filtra por autor y comprueba sus artículos.
  await page.getByRole('textbox', { name: 'Autor' }).click();
  await page.getByRole('textbox', { name: 'Autor' }).fill('Juan David Salazar');
  await page.getByRole('button', { name: 'Filtrar' }).click();
  await expect(articulo2).toBeVisible();
  await expect(estamosMelos).toBeVisible();
  await page.screenshot({ path: 'evidencias/E2E-11-comite-autor.png', fullPage: true });

  // Limpia el autor.
  await page.getByRole('button', { name: 'Limpiar' }).click();
  await expect(page.getByRole('textbox', { name: 'Autor' })).toHaveValue('');

  // Selecciona la conferencia y lee su nombre.
  await page.getByLabel('Conferencia', { exact: true }).selectOption('4');
  const conferencia = await page.getByLabel('Conferencia', { exact: true }).locator('option:checked').innerText();
  await page.getByRole('button', { name: 'Filtrar' }).click();

  // Comprueba los artículos de la conferencia.
  await expect(page.locator('tbody tr td:nth-child(3)').filter({ hasNotText: conferencia })).toHaveCount(0);
  await expect(articulo2).toBeVisible();
  await expect(estamosMelos).toBeVisible();
  await page.screenshot({ path: 'evidencias/E2E-11-comite-conferencia.png', fullPage: true });

  // Limpia la conferencia.
  await page.getByRole('button', { name: 'Limpiar' }).click();
  await expect(page.getByLabel('Conferencia', { exact: true })).toHaveValue('');

  // Filtra por estado y comprueba los artículos en revisión.
  await page.getByLabel('Estado').selectOption('en_revision');
  await page.getByRole('button', { name: 'Filtrar' }).click();
  await expect(page.locator('tbody tr td:nth-child(4)').filter({ hasNotText: 'En revisión' })).toHaveCount(0);
  await expect(page.getByRole('cell', { name: 'Articulo 1', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Articulo sobre IA de prueba', exact: true })).toBeVisible();
  await page.screenshot({ path: 'evidencias/E2E-11-comite-estado.png', fullPage: true });

  // Limpia el estado y comprueba el listado.
  await page.getByRole('button', { name: 'Limpiar' }).click();
  await expect(page.getByLabel('Estado')).toHaveValue('');
  await expect(articulo2).toBeVisible();
  await expect(estamosMelos).toBeVisible();
  await page.screenshot({ path: 'evidencias/E2E-11-comite-limpiar.png', fullPage: true });
});

test('E2E-11 (error): el autor no ve artículos ajenos', async ({ page }) => {
  // Lee la contraseña del autor.
  const password = process.env.E2E_AUTOR_PASSWORD;
  expect(password, 'Define E2E_AUTOR_PASSWORD antes de ejecutar la prueba').toBeTruthy();

  // Abre el login.
  await page.goto('http://localhost:5173/login');

  // Llena el correo del autor.
  await page.getByRole('textbox', { name: 'Correo electrónico' }).click();
  await page.getByRole('textbox', { name: 'Correo electrónico' }).fill('juandavid@teste2e.com');

  // Llena la contraseña.
  await page.getByRole('textbox', { name: 'Contraseña' }).click();
  await page.getByRole('textbox', { name: 'Contraseña' }).fill(password);

  // Marca el captcha.
  const captcha = page
    .frameLocator('iframe[title="reCAPTCHA"]')
    .getByRole('checkbox');
  await captcha.press('Space');
  await expect(captcha).toBeChecked();

  // Inicia sesión y abre Artículos.
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  await page.getByRole('link', { name: 'Artículos' }).click();

  // Busca un artículo de otro autor.
  await page.getByRole('textbox', { name: 'Título' }).click();
  await page.getByRole('textbox', { name: 'Título' }).fill('Prueba Jose');
  await page.getByRole('button', { name: 'Filtrar' }).click();

  // Comprueba que no hay resultados ni artículos ajenos en la tabla.
  await expect(page.getByText('No se encontraron artículos.', { exact: true })).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(0);
  await expect(page.getByRole('cell', { name: 'Prueba Jose', exact: true })).toHaveCount(0);

  // Captura el resultado.
  await page.screenshot({ path: 'evidencias/E2E-11-autor-articulo-ajeno.png', fullPage: true });
});
