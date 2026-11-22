import { test, expect } from '@playwright/test';

// Inicia sesion antes de cada prueba
test.beforeEach(async ({ page }) => {
  await page.goto('/login'); // goto abre la página de login
  await page.getByRole('textbox', { name: 'Correo electrónico' }).fill('autor.jose@prueba.com'); // Busca el componente
  await page.getByRole('textbox', { name: 'Contraseña' }).fill('ClaveSegura123');
  const captcha = page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox');
  await captcha.press('Space');
  await expect(captcha).toBeChecked(); // Confirma que quedo marcado el captcha antes de iniciar sesion
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
});

// Se crea la prueba con su nombre
test('E2E-13: editar un artículo guarda los cambios', async ({ page }) => {
  // Aqui inicia e camino para editar un articulo, primero se hace click en el link de articulos, luego en el link del articulo que se quiere editar y finalmente en el boton de editar
  await page.getByRole('link', { name: 'Artículos' }).click();
  await page.getByRole('link', { name: 'Ver detalle de Articulo editable e2e' }).click();
  await page.getByRole('link', { name: 'Editar' }).click();

  const titulo = `Articulo editable e2e ${Date.now()}`;
  await page.getByRole('textbox', { name: 'Título' }).fill(titulo);
  await page.getByRole('textbox', { name: 'Resumen' }).fill('Este es un resumen de pruebas para las pruebas e2e, estoy editando el articulo para hacer la prueba');
  await page.getByRole('button', { name: 'Guardar cambios' }).click(); // Hasta aqui que guarda los cambios con un click

  // Verifica y deja evidencias, convierte la grabacion en una prueba
  await expect(page.getByText('Artículo actualizado correctamente.')).toBeVisible();
  await expect(page.getByRole('heading', { name: titulo })).toBeVisible();
  await page.screenshot({ path: 'evidencias/E2E-13-editar.png' });
});

test('E2E-13: no permite editar un artículo con la postulación cerrada', async ({ page }) => {
  await page.getByRole('link', { name: 'Artículos' }).click();
  await page.getByRole('link', { name: 'Ver detalle de Articulo de prueba para e2e' }).click();

  // Espera a que cargue el detalle antes de revisar que no este el boton Editar
  await expect(page.getByRole('heading', { name: 'Articulo de prueba para e2e' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Editar' })).toHaveCount(0);

  // Intenta entrar directo a la pagina de edicion
  await page.goto(page.url() + '/editar');
  await expect(page.getByText('La postulación de esta conferencia ya cerró')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Guardar cambios' })).toBeDisabled();
  await page.screenshot({ path: 'evidencias/E2E-13-editar-cerrado.png' });
});
