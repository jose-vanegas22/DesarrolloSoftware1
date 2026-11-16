import { test, expect } from '@playwright/test';

// Se crea la prueba con su nombre
test('E2E-13: editar un artículo guarda los cambios', async ({ page }) => {
  await page.goto('/login'); // goto abre la página de login
  await page.getByRole('textbox', { name: 'Correo electrónico' }).fill('autor.jose@prueba.com'); // Busca el componente
  await page.getByRole('textbox', { name: 'Contraseña' }).fill('ClaveSegura123');
  const captcha = page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox');
  await captcha.press('Space');
  await expect(captcha).toBeChecked(); // Confirma que quedo marcado el captcha antes de iniciar sesion
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();

  // Aqui inicia e camino para editar un articulo, primero se hace click en el link de articulos, luego en el link del articulo que se quiere editar y finalmente en el boton de editar
  await page.getByRole('link', { name: 'Artículos' }).click();
  await page.getByRole('link', { name: 'Ver detalle de Articulo de prueba para e2e' }).click();
  await page.getByRole('link', { name: 'Editar' }).click();

  const titulo = `Articulo de prueba para e2e ${Date.now()}`;
  await page.getByRole('textbox', { name: 'Título' }).fill(titulo);
  await page.getByRole('textbox', { name: 'Resumen' }).fill('Este es un resumen de pruebas para las pruebas e2e, estoy editando el articulo para hacer la prueba');
  await page.getByRole('button', { name: 'Guardar cambios' }).click(); // Hasta aqui que guarda los cambios con un click

  // Verifica y deja evidencias, convierte la grabacion en una prueba
  await expect(page.getByText('Artículo actualizado correctamente.')).toBeVisible();
  await expect(page.getByRole('heading', { name: titulo })).toBeVisible();
  await page.screenshot({ path: 'evidencias/E2E-13-editar.png' });
});
