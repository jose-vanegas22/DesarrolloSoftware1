# Integracion continua de Conecta

CI comprueba el backend, el frontend y las copias E2E aisladas antes de integrar
cambios a `main`. El flujo esta en `.github/workflows/ci.yml` y usa GitHub Actions.
No despliega la aplicacion ni modifica la base de datos compartida.

## Cuando se ejecuta

- Al abrir o actualizar un pull request dirigido a `main`.
- Al hacer push a `main`, incluidos los cambios que llegan mediante un merge.
- Manualmente con `workflow_dispatch`, cuando el workflow ya existe en la rama
  predeterminada del repositorio y el usuario tiene permiso para ejecutarlo.

Un push a otra rama, sin PR hacia `main`, no activa automaticamente este flujo.
No se configuraron filtros por archivos: todos los PR a `main` reciben los mismos
checks. Si llegan cambios nuevos a la misma referencia mientras se ejecuta CI,
se cancela la ejecucion anterior para comprobar la version mas reciente.

## Jobs y responsabilidades

Los tres jobs son independientes y pueden ejecutarse en paralelo en maquinas
Ubuntu de GitHub. Backend y frontend tienen un limite de 15 minutos; E2E,
de 20 minutos. El token del workflow solo tiene permiso de lectura del
contenido del repositorio.

| Job | Comprobaciones | Lo que permite detectar |
| --- | --- | --- |
| Backend | `check`, `makemigrations --check --dry-run` y tests con coverage.py | Problemas de configuracion, cambios de modelos sin migracion y fallos en las pruebas existentes. |
| E2E | Preparacion de datos, arranque de servidores y Playwright sobre PostgreSQL aislado | Fallos en los recorridos de las copias CI. |
| Frontend | `npm run lint` y `npm run build` | Incumplimientos de las reglas de ESLint y errores al construir el frontend. |

Se fijan Python 3.14 y Node 26, correspondientes a las versiones principales
usadas en la validacion local inicial. Las acciones oficiales `setup-python` y
`setup-node` preparan los entornos. La cache de paquetes reduce descargas, pero
las dependencias se instalan en cada job. Backend instala `requirements-ci.txt`,
que incluye `requirements.txt` y coverage.py. E2E instala `requirements.txt`,
las dependencias de frontend/Playwright y Chromium. npm utiliza `npm ci` con
los archivos `package-lock.json`.

Un paso que termina con error hace fallar su job; no se ignoran fallos ni se
desactivan pruebas. Los pasos normales siguientes se omiten, pero los pasos
de reportes y subida con `always()` intentan conservar lo generado. Los otros
jobs pueden continuar. No hay dependencias entre estos jobs.

## Datos y configuracion

El job backend usa `--settings=config.settings_ci`:

- PostgreSQL 18 en un servicio temporal. Django crea y descarta `test_conecta_ci`.
- Archivos de prueba en memoria, sin subir PDF a Supabase Storage.
- Clave de firma ficticia y exclusiva para pruebas; correo en memoria.

El job E2E usa su propio PostgreSQL, `settings_e2e` y una
carpeta temporal para PDF y correos. La configuracion, comandos y limites
se explican en [Entorno de pruebas con PostgreSQL](entorno-e2e.md).

El job de backend no copia el `.env` ni necesita credenciales de Supabase.
Las migraciones se aplican a la base temporal durante las pruebas; el paso
`makemigrations --check --dry-run` no escribe migraciones.

El frontend compila con los valores publicos de `.env.example`: URL local de la
API y clave publica de prueba de reCAPTCHA. El build no arranca la aplicacion,
no llama al backend y no se publica como despliegue. No se necesitan GitHub
Secrets para estos entornos de prueba.

## Ejecutar las mismas comprobaciones localmente

Desde `backend/`, con el entorno virtual activado, las dependencias instaladas
y el PostgreSQL exclusivo de pruebas iniciado como explica la guia del entorno:

```bash
export CONECTA_TEST_DB_PORT=55432  # Puerto del ejemplo Docker de la guia.
python manage.py check --settings=config.settings_ci
python manage.py makemigrations --check --dry-run --settings=config.settings_ci
mkdir -p reportes/cobertura
python -m coverage run manage.py test --settings=config.settings_ci --noinput --verbosity 2
python -m coverage report
python -m coverage html
python -m coverage xml
python -m coverage json
```

Si solo se necesitan los tests, sin cobertura, usar
`python manage.py test --settings=config.settings_ci --noinput --verbosity 2`.

Como alternativa rapida local, `--settings=config.settings_test` sigue usando
SQLite en memoria; no comprueba el comportamiento especifico de PostgreSQL.

Desde `frontend/`, con las dependencias instaladas:

```bash
npm run lint
npm run build
```

En una copia limpia, instalar antes las dependencias con
`python -m pip install -r requirements-ci.txt` en backend y `npm ci` en frontend.
Para reproducir el build de CI, usar los valores de `frontend/.env.example`.
No sobrescribir un `.env` personal que contenga configuracion necesaria.

`--noinput` evita preguntas interactivas y `--verbosity 2` muestra cada prueba.
Sin etiquetas despues de `test`, Django descubre las pruebas `test*.py` de las
apps, incluidos `tests.py` y los archivos `test_*.py` separados.

## Leer los resultados en GitHub

Abrir la pestana Actions, elegir CI y abrir la ejecucion del commit o PR.
Revisar los jobs y el primer paso que falle. El log de Django muestra el
nombre y resultado de cada prueba; ESLint muestra los archivos y reglas que
fallen. Se generan cobertura del backend y reportes/evidencias E2E, y el workflow
los conserva como artifacts durante 30 dias, incluso si fallan los tests. Ver
[reportes, evidencias y cobertura](reportes-pruebas.md).

## Reglas para integrar cambios

El equipo trabaja en una rama por historia y abre un PR hacia `main`; los
commits llevan la clave de Jira al inicio, como indica el README. Antes de
integrar, revisar el codigo, los resultados y cualquier limitacion documentada.
No omitir tests ni eliminar aserciones para conseguir un check verde.

La proteccion de `main` se configura en GitHub por un administrador; el YAML
no la activa. El ensayo anterior confirmado por el equipo bloqueo un merge
con pruebas fallidas y lo habilito tras corregirlas. Esto no acredita que no
existan excepciones o permisos de bypass: su configuracion debe comprobarse
en el ruleset, no deducirse del resultado de un unico usuario.

Los nombres existentes de checks se conservan:

- `Backend - comprobaciones y pruebas`
- `Frontend - lint y build`

El nuevo check es `E2E - recorridos aislados`. Una vez validado en GitHub,
el administrador debe añadirlo a los checks requeridos si se quiere que su
fallo bloquee el merge. Un job rojo no equivale por si solo a una regla de
proteccion obligatoria. No integrar los archivos usados para fallos deliberados.

## E2E y evidencias

Los originales del equipo permanecen en `e2e/tests/`, con su configuracion
habitual. Las copias adaptadas estan en `e2e/tests-ci/`. La configuracion
`playwright.ci.config.js` arranca Django y el frontend compilado, espera su
disponibilidad y restablece datos antes de cada caso/reintento con un worker.
No se reutilizan servidores ajenos ni la base compartida de Supabase.

`CI=1` no crea PostgreSQL ni exporta las variables de conexion. Para ejecutarlo
localmente, seguir la secuencia completa de [preparacion del entorno](entorno-e2e.md).
Con esa preparacion, desde `e2e/`:

```bash
CI=1 npx playwright test --config=playwright.ci.config.js
npx playwright show-report
```

El workflow intenta conservar artifacts de cobertura y E2E durante 30 dias,
tambien ante un fallo. No se versionan reportes ni capturas generadas. La guia
[de reportes y cobertura](reportes-pruebas.md) explica descarga, limites de
retencion, interpretacion de porcentajes y comandos locales.

## Estado de validacion

Los ensayos iniciales en GitHub comprobaron la ejecucion del backend y frontend
al abrir/actualizar un PR, un fallo deliberado y su correccion. La proteccion de
merge se comprobo en otro ensayo confirmado por el equipo. Estas verificaciones
historicas no sustituyen la del job E2E y la subida de artifacts nuevos.

En la validacion local de esta version pasaron 82 tests Django con PostgreSQL
y 26 casos E2E con datos aislados. La cobertura medida de `backend/apps` fue
67,05 % de lineas y 43,70 % de ramas; no representa cobertura del frontend ni
del proyecto entero. El usuario tambien confirmo que pudo repetir los 26 casos
tras configurar el contenedor y las variables locales.

Quedan pendientes la comprobacion del job E2E en GitHub, la descarga real de
artifacts y el fallo controlado del flujo nuevo. El registro de la validacion
final distinguira lo ejecutado localmente de lo comprobado en el runner.

Los casos E2E de crear conferencia y configurar fechas limite no estan en la
version revisada; su incorporacion sigue pendiente segun el inventario. Ademas,
se detectaron respuestas tardias que sobrescriben estado en el frontend de
desarrollo: estan documentadas y no se consideran corregidas por ejecutar el
build de produccion. Las pruebas de acceso de otra rama tampoco forman parte
de las 82 pruebas actuales hasta que se integren.
