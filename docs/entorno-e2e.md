# PostgreSQL para pruebas del backend y E2E

Las pruebas no usan Supabase: emplean un servidor PostgreSQL desechable. En
GitHub Actions lo inicia automaticamente un contenedor de servicio; localmente
puede utilizarse un contenedor o una instalacion propia exclusiva de pruebas.

## Como se conectan las piezas

Playwright -> navegador -> React -> API Django -> ORM -> PostgreSQL (conecta_e2e)

El ORM traduce las operaciones de los modelos a SQL. Las migraciones crean las
tablas y restricciones. `psycopg`, ya incluido en las dependencias, transporta
las consultas entre Django y PostgreSQL. Playwright interactua con la interfaz;
la aplicacion accede a los datos a traves de la API.

| Configuracion | Base y ciclo de vida | Uso |
| --- | --- | --- |
| `settings_test.py` | SQLite en memoria; Django la crea y descarta. | Alternativa local rapida, sin servidor PostgreSQL. |
| `settings_ci.py` | Django crea `test_conecta_ci`, aplica migraciones y la elimina al terminar. | Todos los tests del backend en CI, incluidas las pruebas de integracion. |
| `settings_e2e.py` | Base vacia `conecta_e2e` o con prefijo `conecta_e2e_`; se migra y puebla antes de iniciar la API. | Estado compartido entre el comando de preparacion y el servidor E2E. |

## Configuracion y aislamiento

| Archivo | Responsabilidad |
| --- | --- |
| [postgres_pruebas.py](../backend/config/postgres_pruebas.py) | Comparte la conexion PostgreSQL entre ambas configuraciones de pruebas. Solo conecta a `127.0.0.1`. |
| [settings_ci.py](../backend/config/settings_ci.py) | Conserva archivos y correo en memoria, firma ficticia y hash rapido; sustituye SQLite por PostgreSQL. |
| [settings_e2e.py](../backend/config/settings_e2e.py) | PostgreSQL exclusivo, PDF locales, correo en archivos, firma ficticia y autenticacion habitual. |
| [urls_e2e.py](../backend/config/urls_e2e.py) | Conserva las rutas de la API y sirve `/media/` desde la carpeta local de PDF. No configura la base de datos. |
| [preparar_e2e.py](../backend/apps/usuarios/management/commands/preparar_e2e.py) | Exige base sin tablas y carpeta vacia; aplica migraciones y crea las precondiciones del inventario. |

No se usan las variables `DB_*` de Supabase. La conexion utiliza variables
separadas: `CONECTA_TEST_DB_PORT` (5432 por defecto), `CONECTA_TEST_DB_USER`
(`conecta_test`) y `CONECTA_TEST_DB_PASSWORD` (`conecta_test_local`). Son valores
ficticios para un servidor desechable, nunca credenciales del equipo. No deben
utilizarse para un servidor publicado en Internet. No se modifica el `.env`.

`CONECTA_E2E_DB_NAME` permite elegir una base nueva con el prefijo indicado.
`CONECTA_E2E_DIR` debe ser una carpeta temporal existente con ruta absoluta.
El comando rechaza carpetas usadas, bases con tablas y otra configuracion de
Django. No ejecuta `flush`, no borra bases ni elimina archivos. Si se interrumpe
la preparacion, utilizar otra base vacia y otra carpeta.

```text
Servidor PostgreSQL: tablas y registros de conecta_e2e
Carpeta temporal:
  media/           PDF iniciales y los que suba la aplicacion
  correos/         Mensajes emitidos, sin enviarlos por SMTP
  datos-e2e.json    IDs, correos, roles y nombres; no contiene contraseñas
```

`correos/` aparece con el primer mensaje. Localmente la base y los archivos
permanecen al detener Django para poder inspeccionarlos. En CI, cada job usa su
propio servidor y carpeta; GitHub elimina el contenedor al finalizar el job.
No se comparte base entre los jobs ni entre ejecuciones del workflow.
Se fija PostgreSQL 18 en CI.

## Datos que se crean

- Diez usuarios activos: los perfiles de login, bloqueo, multirrol, autores,
  comites y administrador que requiere el [inventario](inventario-e2e.md).
  Todos empiezan sin intentos fallidos ni bloqueo.
- Dos conferencias activas: una con postulacion abierta durante siete dias
  y otra cuyo plazo termino siete dias antes de la preparacion. Las cuatro
  etapas se calculan respecto al momento de creacion y respetan su orden.
- Ocho articulos: los utilizados en filtros, visibilidad de articulos ajenos,
  edicion con plazo abierto/cerrado y proteccion del autor frente a borrado.
- Un registro de autoria del responsable por articulo y el coautor `coautor2ede`
  que debe poder quitarse de `articulo2`. El responsable de ese articulo tiene
  el nombre `Juan David Salazar`, usado por el filtro de autor.
- Ocho versiones PDF iniciales, guardadas en disco local. Las pruebas de nueva
  postulacion y subida seguiran creando sus propios articulos por la interfaz.

En total quedan preparados 10 usuarios, 2 conferencias, 8 fechas limite,
8 articulos, 9 autorias y 8 archivos PDF.

La conferencia abierta usa el ID fijo `4` para conservar el selector
existente de consulta. Se actualiza la secuencia de PostgreSQL despues de
insertar los IDs fijos para evitar colisiones al crear otras conferencias. Los otros IDs pueden consultarse en `datos-e2e.json`.
Los articulos en revision se preparan en ese estado para probar los filtros;
esta preparacion no representa un ensayo de asignacion de revisores o evaluacion.

Las contraseñas son ficticias y coinciden con los casos existentes:

| Perfil | Contraseña de prueba |
| --- | --- |
| Login de Valencia | `@Valencia1` |
| Bloqueo de Valencia | `@Valencia2` |
| Multirrol de Valencia | `@Valencia3` |
| Demas cuentas preparadas | `ClaveSegura123` |

Que algunos correos coincidan con los scripts actuales no significa que se
usen sus cuentas reales: estos registros solo existen en la nueva base local.

## Errores de conexion y ejecucion local completa

`CI=1` activa opciones de Playwright; **no inicia PostgreSQL, no crea las bases
ni exporta variables**. GitHub hace esos pasos mediante el workflow. Localmente
hay que prepararlos antes.

Si aparece `password authentication failed for user "conecta_test"` en el puerto
5432, Django alcanzo un servidor PostgreSQL, pero ese servidor rechazo las
credenciales. No demuestra un fallo en las pruebas ni que falte psycopg.
El aviso sobre la base `postgres` es consecuencia de la conexion rechazada.
No cambiar la contraseña del PostgreSQL habitual o las credenciales de Supabase
para corregirlo: conectar al servidor exclusivo de pruebas y su puerto correcto.

Para el contenedor de esta guia, el puerto desde la computadora es **55432**;
5432 es el puerto dentro del contenedor. En GitHub se publica en 5432, por eso
ese es el valor predeterminado de la configuracion. Las variables exportadas
solo se conservan en esa terminal y sus procesos hijos.

Despues de iniciar el contenedor de la siguiente seccion y esperar a que acepte
conexiones, ejecutar esta secuencia **en una sola terminal**, desde la raiz del
repositorio. Esta es la opcion automatica: no ejecutar `runserver` manualmente.

```bash
export CONECTA_TEST_DB_PORT=55432
export CONECTA_TEST_DB_USER=conecta_test
export CONECTA_TEST_DB_PASSWORD=conecta_test_local
export E2E_PYTHON="$PWD/backend/venv/bin/python"

cd backend
"$E2E_PYTHON" manage.py test --settings=config.settings_ci --noinput --verbosity 2
cd ..

# Un nombre nuevo evita reutilizar una base con datos de una ejecucion anterior.
export CONECTA_E2E_DB_NAME="conecta_e2e_$(date +%Y%m%d%H%M%S)_$$"
docker exec conecta-postgres-pruebas createdb -U conecta_test "$CONECTA_E2E_DB_NAME"
export CONECTA_E2E_DIR="$(mktemp -d /tmp/conecta-e2e-XXXXXX)"
"$E2E_PYTHON" backend/manage.py preparar_e2e --settings=config.settings_e2e

cd e2e
CI=1 npx playwright test --config=playwright.ci.config.js
```

Continuar solo si cada paso anterior termina correctamente. Los puertos 8000 y
5173 deben estar libres. Si se cambia de terminal, volver a exportar las mismas
variables, incluida la ruta exacta de la carpeta preparada; crear otra carpeta
por si sola no prepara los datos. Si un traceback persiste, sus ultimas lineas
contienen el tipo de excepcion y la causa; las primeras llamadas no bastan.

## Preparar PostgreSQL localmente

Estos ejemplos son para Bash en Linux. Requieren Docker funcionando para la
opcion mostrada y las dependencias habituales del proyecto ya instaladas.
No hace falta instalar Docker localmente para ejecutar CI en GitHub.

Desde cualquier terminal, iniciar un servidor exclusivo de pruebas:

```bash
docker run --name conecta-postgres-pruebas --rm -d \
  -e POSTGRES_USER=conecta_test \
  -e POSTGRES_PASSWORD=conecta_test_local \
  -e POSTGRES_DB=conecta_ci \
  -p 127.0.0.1:55432:5432 postgres:18

docker exec conecta-postgres-pruebas pg_isready -U conecta_test -d conecta_ci
```

Continuar cuando `pg_isready` indique que acepta conexiones. Si el contenedor
aun esta arrancando, repetir esa comprobacion. El puerto 55432 evita ocupar el
5432 de otra instalacion local. Con PostgreSQL instalado directamente, crear
un usuario y bases exclusivos de pruebas; el usuario de los tests Django
necesita permiso `CREATEDB` y acceso a la base administrativa `postgres`.
No usar un servidor compartido con datos del proyecto.

Para ejecutar todos los tests del backend, desde la raiz del repositorio:

```bash
cd backend
source venv/bin/activate
export CONECTA_TEST_DB_PORT=55432
python manage.py check --settings=config.settings_ci
python manage.py makemigrations --check --dry-run --settings=config.settings_ci
python manage.py test --settings=config.settings_ci --noinput --verbosity 2
```

`conecta_ci` es la base de conexion; el ejecutor prueba sobre `test_conecta_ci`.
`--noinput` evita preguntas interactivas: si quedo una base de tests del mismo
nombre, Django puede recrearla. Por eso este servidor debe ser exclusivo de
pruebas. No ejecutar dos suites simultaneas contra el mismo `test_conecta_ci`.

Referencia: [bases de datos de pruebas de Django](https://docs.djangoproject.com/en/6.1/topics/testing/overview/).

## Preparar y ejecutar el backend E2E manualmente

Crear una base E2E vacia en ese servidor (solo una vez para ese nombre):

```bash
docker exec conecta-postgres-pruebas createdb -U conecta_test conecta_e2e
```

Desde `backend/`, con el entorno virtual activado:

```bash
export CONECTA_TEST_DB_PORT=55432
export CONECTA_E2E_DB_NAME=conecta_e2e
export CONECTA_E2E_DIR="$(mktemp -d /tmp/conecta-e2e-XXXXXX)"
python manage.py preparar_e2e --settings=config.settings_e2e
python manage.py check --settings=config.settings_e2e
python manage.py runserver 127.0.0.1:8000 --settings=config.settings_e2e --noreload
```

No ejecutar `migrate` antes de `preparar_e2e`: el comando exige una base vacia
y aplica las migraciones. Imprime el nombre de la base y la ruta del JSON.
Iniciar el servidor en la misma terminal para conservar las variables. Detener
antes cualquier otro servidor que ocupe 8000 o 5173.

Para repetir desde cero sin borrar datos anteriores, crear otra base, por
ejemplo `conecta_e2e_segunda`, exportar ese nombre y crear otra carpeta con
`mktemp`. Una carpeta nueva no reinicia una base existente.

Los enlaces PDF apuntan a `http://127.0.0.1:8000/media/`. `urls_e2e.py` permite
que Django entregue esos archivos durante las pruebas, ya que aqui no se usa
Supabase Storage. Solo se selecciona con `settings_e2e`; no es una configuracion
de despliegue.

Al terminar y tras detener Django, `docker stop conecta-postgres-pruebas`
elimina el contenedor temporal y sus bases por usar `--rm`, sin volumen
persistente. Las carpetas creadas con `mktemp` se conservan para inspeccion y
pueden eliminarse cuando dejen de necesitarse.

## GitHub Actions

El workflow declara un servicio `postgres:18` independiente en cada job que
necesita datos. Define usuario, contraseña ficticia y base inicial. El chequeo
`pg_isready` espera a que el servidor acepte conexiones antes de ejecutar pasos.
Los procesos Python corren en Ubuntu y acceden al puerto local 5432 del servicio.

- `Backend - comprobaciones y pruebas`: ejecuta la suite existente con
  `settings_ci`.
- `E2E - recorridos aislados`: prepara PostgreSQL y los datos, instala frontend,
  Playwright y Chromium, y ejecuta las copias de `tests-ci/`. Playwright inicia
  y detiene los servidores mediante `webServer`. Su limite es de 20 minutos.
- `Frontend - lint y build`: conserva sus comprobaciones actuales.

Los dos servicios pueden publicar el puerto 5432 porque sus jobs se ejecutan
en maquinas distintas. No hay que crear bases en Supabase ni configurar
GitHub Secrets para estas credenciales ficticias. Los reportes y capturas se publican como artifacts durante 30 dias; ver
[reportes y cobertura](reportes-pruebas.md).

Referencia: [servicios PostgreSQL en GitHub Actions](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers).

## Frontend y variables de las pruebas

En otra terminal, desde la raiz:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8000/api \
VITE_RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI \
npm run dev -- --host localhost --port 5173 --strictPort
```

Se pasan valores al proceso sin sobrescribir el `.env`. En la terminal donde
se vaya a ejecutar Playwright, definir:

```bash
export E2E_AUTOR_PASSWORD='ClaveSegura123'
export E2E_COMITE_PASSWORD='ClaveSegura123'
export E2E_CORREO='autor.jose@prueba.com'
export E2E_PASSWORD='ClaveSegura123'
```

La configuracion E2E usa la clave publica de pruebas del backend de reCAPTCHA
v2 y el frontend usa su pareja. Son las claves que Google publica para pruebas,
no credenciales de una base de datos. El widget se carga y se consulta Google,
por lo que **las pruebas requieren acceso de red al servicio de CAPTCHA**. El
login no tiene ningun bypass ni se simula la API de la aplicacion.
Referencia: [claves de pruebas de reCAPTCHA](https://developers.google.com/recaptcha/docs/faq).

Los correos se escriben mediante el backend de archivos de Django, con
`MAILERS`. No salen a destinatarios reales. Referencia:
[correo en archivos](https://docs.djangoproject.com/en/6.1/topics/email/#file-backend).

## Adaptacion de los recorridos existentes

Los originales del equipo permanecen intactos en `e2e/tests/`. Las copias
adaptadas de los 26 casos estan en `e2e/tests-ci/`, con los mismos 12 nombres
de archivo. Solo estas copias importan
`test` desde `e2e/soporte/entorno.js`, que añade una fixture automatica: una
preparacion que Playwright ejecuta antes de cada caso, incluidos sus reintentos.
No se sustituyen las operaciones de negocio ni sus respuestas por simulaciones.
El CAPTCHA conserva el widget y la consulta externa con claves de pruebas.

La configuracion `playwright.ci.config.js` selecciona exclusivamente `tests-ci/`
y activa `E2E_AISLADO=1`. Antes de ejecutar los casos:

1. Preparar una base y carpeta nuevas con `preparar_e2e`, como se explica arriba.
2. Dejar libres los puertos 8000 y 5173; Playwright iniciara ambos servidores.
3. En la terminal de Playwright exportar **los mismos** `CONECTA_E2E_DIR`,
   `CONECTA_E2E_DB_NAME`, `CONECTA_TEST_DB_PORT` y las credenciales de prueba si
   se cambiaron sus valores predeterminados.
4. Seleccionar `--config=playwright.ci.config.js`. `E2E_PYTHON` permite indicar la ruta absoluta del
   Python con las dependencias instaladas; por defecto usa `backend/venv/bin/python`.
   En GitHub se podra usar `E2E_PYTHON=python`.

Se puede comprobar el descubrimiento, sin iniciar servidores ni cambiar datos:

```bash
cd e2e
npx playwright test --config=playwright.ci.config.js --list --reporter=list
```

### Restablecimiento antes de cada caso

La fixture comprueba primero `/api/e2e/entorno/`: la API debe usar las rutas E2E
con la misma base y carpeta que Playwright. Esta ruta solo identifica el entorno;
no inicia sesiones ni modifica datos y no existe en las rutas habituales.

Despues ejecuta `restablecer_e2e` mediante el Python del backend. Este comando
**vacia los datos de la base E2E preparada**, limpia sus carpetas `media` y
`correos` y vuelve a crear las precondiciones. Exige `settings_e2e`, conexion
local, nombre de base E2E, almacenamiento local y un manifiesto de preparacion
que coincida con la base.

Esto restaura el coautor eliminado, los bloqueos, perfiles, titulos y tokens,
y elimina los usuarios y articulos generados por el caso anterior. Se hace al
principio para conservar los datos del ultimo caso al terminar, incluso si falla.
No hace falta esperar 15 minutos ni restaurar el coautor manualmente.

Como todos los casos usan esta misma base, el modo aislado exige **un worker**.
La configuracion desactiva el paralelismo de ese modo; la fixture rechaza un
`--workers` superior a uno. Un bloqueo de carpeta evita dos ejecuciones sobre
el mismo entorno. No ejecutar suites simultaneas con carpetas diferentes sobre
una misma base. Si se interrumpe abruptamente el proceso, el bloqueo puede
permanecer: preparar un entorno nuevo antes de repetir.

Las contraseñas de las cuentas preparadas se usan automaticamente en modo
aislado, sin depender de contraseñas privadas exportadas en la terminal.
La conferencia abierta se selecciona por nombre en ese modo. El recorrido de
login, CAPTCHA, formulario y comprobaciones sigue ejecutandose realmente.

### Evidencias y modo manual

En modo aislado las capturas explicitas usan `testInfo.outputPath`: quedan en
`e2e/test-results/`, separadas por caso y reintento. No sobrescriben las imagenes
versionadas de `e2e/evidencias/`. Los adjuntos existentes de postulacion y PDF
se conservan. El workflow publica estas carpetas como artifacts durante 30 dias.

El comando habitual `npx playwright test` conserva la configuracion original
`playwright.config.js` y ejecuta solo `tests/`, sin usar la fixture de CI.
Sus capturas y precondiciones siguen funcionando como las definio el equipo.
Las copias en `tests-ci/` requieren la configuracion CI incluso localmente;
no se permite ejecutarlas accidentalmente sin aislamiento.

La configuracion CI reutiliza las opciones comunes de la original y cambia
la carpeta de casos, el paralelismo y el arranque de servidores. Ambos
conjuntos se descubren por separado: no se ejecutan 52 casos por duplicado.
Si un compañero corrige un recorrido original, revisar y trasladar el cambio
funcional a su copia CI, conservando su preparacion aislada. Las copias no se
sincronizan automaticamente; esta separacion requiere ese mantenimiento.

La adaptacion conserva los 26 casos y sus aserciones.
Referencia: [fixtures de Playwright](https://playwright.dev/docs/test-fixtures).

## Arranque automatico y ejecucion de las copias CI

Con PostgreSQL iniciado y el entorno preparado, desde `e2e/`:

```bash
# Exportar los valores de la base y carpeta preparados en esta misma ejecucion.
# CONECTA_E2E_DIR debe coincidir con la carpeta usada por preparar_e2e.
npx playwright test --config=playwright.ci.config.js
```

No iniciar antes `runserver` ni Vite. `playwright.ci.config.js` declara dos
servidores con `webServer`:

- Backend: `soporte/servidor-backend.cjs` ejecuta Python con `settings_e2e`
  y `--noreload` en el puerto 8000. Usa `E2E_PYTHON` o el Python del entorno
  virtual del proyecto. Espera una respuesta de `/api/e2e/entorno/`.
- Frontend: compila con `npm run build` y sirve el resultado con `vite preview`
  en localhost:5173 y `--strictPort`, con la URL local de
  API y la clave publica de pruebas de CAPTCHA, sin sobrescribir `.env`.
  Espera una respuesta de `/login`.

Cada servidor tiene hasta 60 segundos para iniciar. `reuseExistingServer: false`
impide reutilizar accidentalmente un servidor habitual; si el puerto ya esta
ocupado, detener ese servidor y repetir. Playwright termina los procesos que
inicio al finalizar, incluso con pruebas fallidas. PostgreSQL y los datos
locales se conservan hasta que se detenga su servidor o contenedor.

Antes de cada caso, la fixture verifica la identidad del backend y restablece
las precondiciones. Las pruebas siguen usando la API real y reCAPTCHA de Google;
por tanto, requieren acceso de red al servicio externo.

### Resultados locales frente a artifacts

Se generan los siguientes resultados locales, que CI publica como artifacts:

- `e2e/playwright-report/`: reporte HTML. No se abre automaticamente para evitar
  dejar un servidor de reportes activo al fallar la ejecucion.
- `e2e/test-results/`: capturas explicitas y capturas de fallos; se retienen trazas de los intentos fallidos, salvo los casos que
  las deshabilitan expresamente. Tambien incluye `resultados.json`.
- Consola: resultado de cada caso y errores de los servidores.

Para consultar el reporte terminado, desde `e2e/`:

```bash
npx playwright show-report
```

Estas carpetas estan ignoradas por `e2e/.gitignore`. Las imagenes versionadas
en `evidencias/` no se sobrescriben. Playwright reutiliza
las carpetas de salida: copiar un reporte antes de otra ejecucion si se desea
conservarlo. En GitHub, los logs del job quedan consultables, pero los archivos
HTML, capturas, JSON y trazas disponibles se suben mediante `upload-artifact`
y se conservan durante 30 dias. Ver [reportes y cobertura](reportes-pruebas.md).

Referencia: [arranque de servidores con Playwright](https://playwright.dev/docs/test-webserver).
