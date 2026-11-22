import { test, expect } from '@playwright/test';

// No graba credenciales en trazas ni videos.
test.use({ trace: 'off', video: 'off' });

test('E2E-12: el autor quita un coautor desde el detalle', async ({ page }) => {
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

  // Abre el detalle del artículo.
  await page.getByRole('link', { name: 'Ver detalle de articulo2', exact: true }).click();
  const autores = page.locator('.detalle-autores');
  const coautor = autores.getByRole('listitem').filter({
    has: page.getByText('coautor2ede', { exact: true }),
  });
  const responsable = autores.getByRole('listitem').filter({ hasText: 'juandavid@teste2e.com' });

  // Pide quitar al coautor.
  await page.getByRole('button', { name: 'Quitar a coautor2ede', exact: true }).click();

  // Comprueba el nombre y confirma en el cuadro de diálogo.
  const modal = page.getByRole('dialog');
  await expect(modal).toContainText('coautor2ede');

  await modal.getByRole('button', { name: 'Quitar coautor', exact: true }).click();

  // Comprueba el mensaje y que el coautor desapareció.
  await expect(page.getByText('Coautor quitado correctamente.', { exact: true })).toBeVisible();
  await expect(modal).toHaveCount(0);
  await expect(coautor).toHaveCount(0);
  await expect(responsable).toBeVisible();
  await expect(responsable).toContainText('Responsable');

  // Captura el resultado.
  await page.screenshot({ path: 'evidencias/E2E-12-coautor-quitado.png', fullPage: true });

  // Recarga para comprobar que el cambio quedó guardado.
  await page.reload();
  await expect(page.getByRole('heading', { name: 'articulo2', exact: true })).toBeVisible();
  await expect(responsable).toBeVisible();
  await expect(responsable).toContainText('Responsable');
  await expect(coautor).toHaveCount(0);

  // Captura el artículo después de recargar.
  await page.screenshot({ path: 'evidencias/E2E-12-coautor-quitado-recarga.png', fullPage: true });
});
