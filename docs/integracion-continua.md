# Integracion continua de Conecta

La primera version de CI comprueba el backend y el frontend antes de integrar
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

Los dos jobs son independientes y pueden ejecutarse en paralelo en maquinas
Ubuntu de GitHub. Cada uno tiene un limite de 15 minutos. El token del workflow
solo tiene permiso de lectura del contenido del repositorio.

| Job | Comprobaciones | Lo que permite detectar |
| --- | --- | --- |
| Backend | `check`, `makemigrations --check --dry-run` y `test` | Problemas de configuracion, cambios de modelos sin migracion y fallos en las pruebas existentes. |
| Frontend | `npm run lint` y `npm run build` | Incumplimientos de las reglas de ESLint y errores al construir el frontend. |

Se fijan Python 3.14 y Node 26, correspondientes a las versiones principales
usadas en la validacion local inicial. Las acciones oficiales `setup-python` y
`setup-node` preparan los entornos. La cache de paquetes reduce descargas, pero
las dependencias se instalan en cada job. Python utiliza `requirements.txt` y
npm utiliza `npm ci` con `package-lock.json`.

Un paso que termina con error hace fallar su job; no se ignoran fallos ni se
desactivan pruebas. Los siguientes pasos del mismo job se omiten y el otro job
puede continuar. No hay dependencias entre los dos jobs.

## Datos y configuracion

Todos los comandos de Django usan `--settings=config.settings_test`:

- Base SQLite temporal en memoria, creada y descartada por el ejecutor de pruebas.
- Archivos de prueba en memoria, sin subir PDF a Supabase Storage.
- Clave de firma ficticia y exclusiva para pruebas.

El job de backend no copia el `.env` ni necesita credenciales de Supabase.
Las migraciones se aplican a la base temporal durante las pruebas; el paso
`makemigrations --check --dry-run` no escribe migraciones.

El frontend compila con los valores publicos de `.env.example`: URL local de la
API y clave publica de prueba de reCAPTCHA. El build no arranca la aplicacion,
no llama al backend y no se publica como despliegue. No se necesitan GitHub
Secrets para esta primera version.

## Ejecutar las mismas comprobaciones localmente

Desde `backend/`, con el entorno virtual activado y las dependencias instaladas:

```bash
python manage.py check --settings=config.settings_test
python manage.py makemigrations --check --dry-run --settings=config.settings_test
python manage.py test --settings=config.settings_test --noinput --verbosity 2
```

Desde `frontend/`, con las dependencias instaladas:

```bash
npm run lint
npm run build
```

En una copia limpia, instalar antes las dependencias con
`python -m pip install -r requirements.txt` en backend y `npm ci` en frontend.
Para reproducir el build de CI, usar los valores de `frontend/.env.example`.
No sobrescribir un `.env` personal que contenga configuracion necesaria.

`--noinput` evita preguntas interactivas y `--verbosity 2` muestra cada prueba.
Sin etiquetas despues de `test`, Django descubre las pruebas `test*.py` de las
apps, incluidos `tests.py` y los archivos `test_*.py` separados.

## Leer los resultados en GitHub

Abrir la pestana Actions, elegir CI y abrir la ejecucion del commit o PR.
Revisar ambos jobs y el primer paso que falle. El log de Django muestra el
nombre y resultado de cada prueba; ESLint muestra los archivos y reglas que
fallen. No se generan aun reportes de cobertura ni se suben artifacts.

Para bloquear merges cuando CI falla, un administrador debe configurar las
reglas de proteccion de `main` y exigir los dos checks. Crear este YAML no
activa por si solo esa proteccion. Los nombres comprobados en GitHub son
`Backend - comprobaciones y pruebas` y `Frontend - lint y build`.
La configuracion y validacion de esa proteccion corresponden a SCRUM-613.

## Validacion inicial (22 de noviembre de 2026)

En la copia local, con Python 3.14.10 y Node 26.13.1:

| Comprobacion | Resultado |
| --- | --- |
| Django `check` | Sin problemas. |
| Migraciones pendientes de generar | Ninguna. |
| Pruebas del backend | 82 pruebas, todas pasan. |
| ESLint | Pasa. |
| Build de Vite | Pasa. |

Se repitieron las comprobaciones en una copia temporal de los archivos
versionados, sin los `.env` privados, y volvieron a pasar las 82 pruebas, lint
y build. No se ejecutaron E2E como parte de esta version de CI.

La validacion de SCRUM-599, subtarea de SCRUM-595, tambien se realizo en
GitHub Actions mediante el [PR de ensayo #48](https://github.com/jose-vanegas22/DesarrolloSoftware1/pull/48),
dirigido a `main` desde `feature/SCRUM-595-prueba-ci`, sin fusionarlo.

| Ensayo | Commit | Backend | Frontend | Evidencia en GitHub |
| --- | --- | --- | --- | --- |
| Apertura del PR | `cf6fefc` | Pasa. | Pasa. | [Ejecucion inicial](https://github.com/jose-vanegas22/DesarrolloSoftware1/actions/runs/45096431015) |
| Actualizacion con fallo deliberado | `892165e` | Falla en la prueba deliberada. | Pasa. | [Fallo controlado](https://github.com/jose-vanegas22/DesarrolloSoftware1/actions/runs/45097866974) |
| Actualizacion tras retirar el fallo | `c9fa5a1` | Pasa. | Pasa. | [Recuperacion](https://github.com/jose-vanegas22/DesarrolloSoftware1/actions/runs/45098659110) |

La instalacion de dependencias y las comprobaciones de ambos jobs pasaron en
los runners de GitHub. El ensayo agrego temporalmente una prueba que fallaba
de forma explicita: se ejecutaron 83 pruebas, con un unico fallo deliberado.
Al retirar ese archivo, las 82 pruebas originales volvieron a pasar. No se
debilitaron las pruebas existentes ni se modifico codigo de negocio.
El fallo solo se incluyo en la rama de ensayo; no forma parte de la rama
definitiva `feature/SCRUM-595-integracion-continua`.

Esto verifica la ejecucion automatica al abrir y actualizar un PR y la
deteccion de una prueba fallida. Queda por comprobar el evento `push` a
`main` cuando se integre el PR definitivo. Estos ensayos no demuestran que
GitHub bloquee un merge con checks fallidos: esa comprobacion pertenece a
SCRUM-613.
