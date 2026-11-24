import { test, expect, rutaEvidencia } from '../soporte/entorno';

// Usuario de prueba con un solo rol: Comité científico
const CORREO = 'comite.cristian@prueba.com';
const PASSWORD = 'ClaveSegura123';

// Inicia sesión igual que una persona: llena el formulario, marca el captcha y entra
async function iniciarSesion(page) {
    await page.goto('/login');
    await page.locator('#login-correo').fill(CORREO);
    await page.locator('#login-password').fill(PASSWORD);
    const captcha = page.frameLocator('iframe[title="reCAPTCHA"]').getByRole('checkbox');
    await captcha.press('Space');
    await expect(captcha).toBeChecked();
    await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
    await expect(page).toHaveURL(/\/inicio/, { timeout: 15000 });
}

// Abre Usuarios > Crear usuario, llena el formulario con el correo indicado y guarda
async function crearUsuario(page, correo) {
    await page.getByRole('link', { name: 'Usuarios' }).click();
    await page.getByRole('button', { name: 'Crear usuario' }).click();

    const modal = page.getByRole('dialog');
    await modal.getByLabel('Nombres').fill('Prueba');
    await modal.getByLabel('Apellidos').fill('E2E Cristian');
    await modal.getByLabel('Correo electrónico').fill(correo);
    await modal.getByLabel('Contraseña', { exact: true }).fill('ClaveSegura123');
    await modal.getByLabel('Confirmar contraseña').fill('ClaveSegura123');
    await modal.getByRole('checkbox', { name: 'Autor' }).check();
    await modal.getByRole('button', { name: 'Guardar usuario' }).click();
    return modal;
}

test('E2E-09: crear un usuario desde administración', async ({ page }) => {
    await iniciarSesion(page);

    // Correo distinto en cada corrida para no chocar con la anterior
    const correo = `nuevo.${Date.now()}@prueba.com`;
    await crearUsuario(page, correo);

    // Verifica el mensaje y que el usuario nuevo aparezca en la lista
    await expect(page.getByText('Usuario creado correctamente.')).toBeVisible();
    await page.getByLabel('Buscar').fill(correo);
    await page.getByRole('button', { name: 'Filtrar' }).click();
    await expect(page.getByRole('cell', { name: correo })).toBeVisible();
    await page.screenshot({ path: rutaEvidencia('E2E-09-exito.png'), fullPage: true });
});

test('E2E-09 (error): no deja crear un usuario con un correo ya registrado', async ({ page }) => {
    await iniciarSesion(page);

    // Usa el correo del usuario con el que se inició sesión, que ya existe
    const modal = await crearUsuario(page, CORREO);

    // El formulario sigue abierto y muestra el error del backend
    await expect(modal).toBeVisible();
    await expect(modal.getByText(/Ya existe un\/a usuario con este\/a correo/)).toBeVisible();
    await page.screenshot({ path: rutaEvidencia('E2E-09-error.png'), fullPage: true });
});