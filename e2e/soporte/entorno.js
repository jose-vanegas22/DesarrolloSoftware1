import { test as base, expect } from '@playwright/test';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdir, rmdir } from 'node:fs/promises';
import path from 'node:path';

export const aislado = process.env.E2E_AISLADO === '1';
export const API = 'http://127.0.0.1:8000/api';

export function passwordPrueba(variable, predeterminada = 'ClaveSegura123') {
  return aislado ? predeterminada : (process.env[variable] ?? predeterminada);
}

export function rutaEvidencia(nombre) {
  return aislado ? test.info().outputPath(nombre) : `evidencias/${nombre}`;
}

export const test = base.extend({
  entornoAislado: [async ({ baseURL, request }, use, testInfo) => {
    if (!aislado) {
      throw new Error('Ejecuta las copias CI con --config=playwright.ci.config.js.');
    }
    if (baseURL !== 'http://localhost:5173' || testInfo.config.workers !== 1) {
      throw new Error('El entorno aislado requiere localhost:5173 y un unico worker.');
    }
    const directorio = process.env.CONECTA_E2E_DIR;
    if (!directorio || !path.isAbsolute(directorio)) {
      throw new Error('Define CONECTA_E2E_DIR igual que en el servidor Django E2E.');
    }
    const respuesta = await request.get(`${API}/e2e/entorno/`);
    if (!respuesta.ok()) throw new Error('La API no es el servidor E2E aislado.');
    const entorno = await respuesta.json();
    if (entorno.directorio !== directorio ||
        entorno.base !== (process.env.CONECTA_E2E_DB_NAME || 'conecta_e2e')) {
      throw new Error('Playwright y Django deben usar la misma carpeta y base E2E.');
    }
    // Impide que dos ejecuciones sobre esta carpeta reinicien datos simultaneamente.
    const bloqueo = path.join(directorio, '.playwright-lock');
    await mkdir(bloqueo);
    try {
      const backend = path.resolve(__dirname, '../../backend');
      const python = process.env.E2E_PYTHON || path.join(backend, 'venv/bin/python');
      await promisify(execFile)(python, [
        'manage.py', 'restablecer_e2e', '--settings=config.settings_e2e',
      ], { cwd: backend, env: process.env, timeout: 60000 });
      await use();
    } finally {
      await rmdir(bloqueo);
    }
  }, { auto: true, timeout: 90000 }],
});

export { expect };
