import { test, expect } from '@playwright/test';

// Usuario de prueba con un solo rol: Comité científico
const CORREO = 'comite.cristian@prueba.com';
const PASSWORD = 'ClaveSegura123';

// Autor real que ya tiene un artículo postulado ("El avance de la IA")
const AUTOR_CON_ARTICULOS = 'cristian.madero@correounivalle.edu.co';

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

// Escribe en el buscador de Usuarios y filtra
async function buscarUsuario(page, texto) {
    await page.getByLabel('Buscar').fill(texto);
    await page.getByRole('button', { name: 'Filtrar' }).click();
}

test('E2E-10: borrar un usuario', async ({ page }) => {
    await iniciarSesion(page);
    await page.getByRole('link', { name: 'Usuarios' }).click();

    // Primero crea un usuario solo para esta prueba, así no se borra a nadie real
    const correo = `borrar.${Date.now()}@prueba.com`;
    await page.getByRole('button', { name: 'Crear usuario' }).click();
    const formulario = page.getByRole('dialog');
    await formulario.getByLabel('Nombres').fill('Borrar');
    await formulario.getByLabel('Apellidos').fill('E2E Cristian');
    await formulario.getByLabel('Correo electrónico').fill(correo);
    await formulario.getByLabel('Contraseña', { exact: true }).fill('ClaveSegura123');
    await formulario.getByLabel('Confirmar contraseña').fill('ClaveSegura123');
    await formulario.getByRole('checkbox', { name: 'Autor' }).check();
    await formulario.getByRole('button', { name: 'Guardar usuario' }).click();
    await expect(page.getByText('Usuario creado correctamente.')).toBeVisible();

    // Lo busca, lo borra y confirma
    await buscarUsuario(page, correo);
    await expect(page.getByRole('cell', { name: correo })).toBeVisible();
    await page.getByRole('row').filter({ hasText: correo }).getByRole('button', { name: /^Borrar a / }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Borrar usuario' }).click();

    // Verifica el mensaje y que ya no aparezca en la lista
    await expect(page.getByText('Usuario borrado correctamente.')).toBeVisible();
    await expect(page.getByRole('cell', { name: correo })).toHaveCount(0);
    await page.screenshot({ path: 'evidencias/E2E-10-exito.png', fullPage: true });
});

test('E2E-10 (error): no deja borrar al administrador ni a un autor con artículos', async ({ page }) => {
    await iniciarSesion(page);
    await page.getByRole('link', { name: 'Usuarios' }).click();

    // 1. Al administrador no le aparece el botón de borrar
    await page.getByLabel('Rol').selectOption('administrador');
    await page.getByRole('button', { name: 'Filtrar' }).click();
    await expect(page.getByRole('button', { name: /^Editar a / }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /^Borrar a / })).toHaveCount(0);
    await page.screenshot({ path: 'evidencias/E2E-10-error-administrador.png', fullPage: true });

    // 2. A un autor con artículos el backend no lo deja borrar
    await page.getByRole('button', { name: 'Limpiar' }).click();
    await buscarUsuario(page, AUTOR_CON_ARTICULOS);
    await expect(page.getByRole('cell', { name: AUTOR_CON_ARTICULOS })).toBeVisible();
    await page.getByRole('row').filter({ hasText: AUTOR_CON_ARTICULOS }).getByRole('button', { name: /^Borrar a / }).click();
    const modal = page.getByRole('dialog');
    await modal.getByRole('button', { name: 'Borrar usuario' }).click();
    await expect(modal.getByText('No se puede borrar porque es autor responsable de artículos.')).toBeVisible();
    await page.screenshot({ path: 'evidencias/E2E-10-error-autor.png', fullPage: true });
    await modal.getByRole('button', { name: 'Cancelar' }).click();
});