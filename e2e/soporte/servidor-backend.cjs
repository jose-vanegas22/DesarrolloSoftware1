// Playwright administra este proceso y su grupo; no se reutiliza un Django ajeno.
const { spawn } = require('node:child_process');
const path = require('node:path');
const { existsSync } = require('node:fs');
const directorio = process.env.CONECTA_E2E_DIR;
if (!directorio || !path.isAbsolute(directorio) ||
    !existsSync(path.join(directorio, 'datos-e2e.json'))) {
  console.error('Falta el entorno E2E preparado. Inicia PostgreSQL de pruebas, ejecuta preparar_e2e y exporta CONECTA_E2E_DIR en esta misma terminal. Consulta docs/entorno-e2e.md. CI=1 no prepara la base de datos.');
  process.exit(1);
}
const backend = path.resolve(__dirname, '../../backend');
const python = process.env.E2E_PYTHON || path.join(backend, 'venv/bin/python');
const servidor = spawn(python, [
  'manage.py', 'runserver', '127.0.0.1:8000',
  '--settings=config.settings_e2e', '--noreload',
], { cwd: backend, env: process.env, stdio: 'inherit' });
servidor.on('error', (error) => { console.error(error); process.exit(1); });
servidor.on('exit', (codigo) => process.exit(codigo ?? 1));
for (const signal of ['SIGTERM', 'SIGINT']) {
  process.on(signal, () => servidor.kill(signal));
}
