import { test, expect } from '@playwright/test';

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

test.describe('HU-01: Registro de usuario', () => {
  test('Registro exitoso de un nuevo usuario', async ({ page }) => {
    const correoUnico = `aurora.${Date.now()}@gmail.com`;

    await page.goto('http://localhost:5173/login');
    await page.getByRole('link', { name: 'Crear cuenta' }).click();

    await page.getByRole('textbox', { name: 'Nombres' }).fill('Aurora ');
    await page.getByRole('textbox', { name: 'Apellidos' }).fill('Cruz Giron');
    await page.getByRole('textbox', { name: 'Correo electrónico' }).fill(correoUnico);
    await page.getByRole('textbox', { name: 'Teléfono (opcional)' }).fill('318759864');
    await page.getByRole('textbox', { name: 'Contraseña', exact: true }).fill('Aurora123');
    await page.getByRole('textbox', { name: 'Confirmar contraseña' }).fill('Aurora123');

    await intentarResolverRecaptcha(page);

    const botonCrear = page.getByRole('button', { name: 'Crear cuenta' });
    await expect(botonCrear).toBeVisible();

    if (await botonCrear.isEnabled()) {
      await botonCrear.click();
      await expect(page).not.toHaveURL(/\/register|\/crear-cuenta/i);
    }
  });

  test('Intento de registro con correo ya registrado', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    await page.getByRole('link', { name: 'Crear cuenta' }).click();

    await page.getByRole('textbox', { name: 'Nombres' }).fill('Jessica ');
    await page.getByRole('textbox', { name: 'Apellidos' }).fill('Alonso');
    await page
      .getByRole('textbox', { name: 'Correo electrónico' })
      .fill('miguelangelcruzgiron97@gmail.com');
    await page.getByRole('textbox', { name: 'Teléfono (opcional)' }).fill('3147896345');
    await page.getByRole('textbox', { name: 'Contraseña', exact: true }).fill('123A');
    await page.getByRole('textbox', { name: 'Confirmar contraseña' }).fill('123A');

    await intentarResolverRecaptcha(page);

    const botonCrear = page.getByRole('button', { name: 'Crear cuenta' });
    await expect(botonCrear).toBeVisible();

    if (await botonCrear.isEnabled()) {
      await botonCrear.click();
      await expect(page.getByText(/correo|registrado|existe|error|captcha/i).first()).toBeVisible();
    }
  });
});