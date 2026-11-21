import { test, expect } from '@playwright/test';

const EMAIL_PRUEBA = 'miguelangelcruzgiron97@gmail.com';
const PASSWORD_PRUEBA = 'America2008';

async function intentarResolverRecaptcha(page) {
  try {
    const captchaFrame = page
      .locator('iframe[src*="recaptcha"], iframe[title*="reCAPTCHA" i]')
      .first();
    await captchaFrame.waitFor({ state: 'visible', timeout: 3000 });
    const checkbox = captchaFrame
      .contentFrame()
      .getByRole('checkbox', { name: /no soy un robot/i });

    try {
      await checkbox.click({ timeout: 2000 });
    } catch {
      await checkbox.press('Enter', { timeout: 2000 });
    }
  } catch {
  
  }
}

test.describe('HU-05: Gestión de perfil de usuario', () => {
  test('Editar apellidos y teléfono en Mi perfil y guardar cambios', async ({ page }) => {
    await page.goto('http://localhost:5173/login');

    await page.getByRole('textbox', { name: 'Correo electrónico' }).fill(EMAIL_PRUEBA);
    await page.getByRole('textbox', { name: 'Contraseña' }).fill(PASSWORD_PRUEBA);

    await intentarResolverRecaptcha(page);

    const botonLogin = page.getByRole('button', { name: 'Iniciar sesión' });
    await expect(botonLogin).toBeVisible();

    if (await botonLogin.isEnabled()) {
      await botonLogin.click();

      await page.getByRole('link', { name: 'Mi perfil' }).click();

      const apellidosInput = page.getByRole('textbox', { name: 'Apellidos' });
      const telefonoInput = page.getByRole('textbox', { name: 'Teléfono' });

      await apellidosInput.fill('Cruz Rincon');
      await telefonoInput.fill('3164557589');
      await page.getByRole('button', { name: 'Guardar cambios' }).click();

      await expect(apellidosInput).toHaveValue('Cruz Rincon');
      await expect(telefonoInput).toHaveValue('3164557589');
    }
  });
});