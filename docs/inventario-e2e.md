# Inventario de casos y precondiciones E2E

Revision del 23 de noviembre de 2026 sobre el codigo integrado en `main`.
Este documento identifica los datos, servicios y cambios de estado que
necesita cada recorrido antes de preparar su ejecucion aislada en CI.
La adaptacion posterior vive en `e2e/tests-ci/`; los originales en `e2e/tests/`
se conservan intactos. Las copias conservan sus aserciones y añaden
restablecimiento antes de cada caso. La configuracion CI automatiza el arranque
y la ejecucion con navegador; los resultados se registran en la guia del entorno. La preparacion posterior de base,
archivos y datos locales se documenta en [Entorno E2E](entorno-e2e.md).

## Alcance encontrado

Playwright descubre **26 casos en 12 archivos**, correspondientes a E2E-03
hasta E2E-14, con Chromium. Son 12 grupos funcionales; varios incluyen mas
de dos casos. El listado no demuestra que las pruebas pasen.

La guia del equipo, `contexto/Guía de pruebas E2E con Playwright (1).pdf`,
paginas 1 y 2, incluye tambien E2E-01 (crear conferencia) y E2E-02 (fechas
limite). Sus archivos no estan en la version de `main` revisada. Se registran
como pendientes de disponibilidad, no como aprobados ni excluidos del sprint.
Confirmar si estan pendientes de integrar antes de cerrar el alcance de CI.
Los nombres de archivo de registro y perfil difieren de los sugeridos en la
guia, pero sus casos estan presentes y se identifican por su ID.

## Casos disponibles y sus precondiciones

Todas las cuentas utilizadas para iniciar sesion deben estar activas, con
contraseña conocida y sin bloqueo previo. Salvo E2E-04, los recorridos esperan
entrar sin pasar por la pantalla de seleccion de rol.

| Grupo y archivo | Casos y comprobaciones | Datos y condiciones previas | Cambios que deja |
| --- | --- | --- | --- |
| E2E-03: [login-bloqueo.spec.js](../e2e/tests/login-bloqueo.spec.js) | 2: login con CAPTCHA; cinco fallos seguidos de rechazo de la contraseña correcta. | Dos autores de un solo rol: `autor.valencia@prueba1.com` y `autor.valencia@prueba2.com`. La segunda cuenta debe empezar desbloqueada. El acceso inicial correcto reinicia el contador. | La segunda cuenta termina bloqueada durante 15 minutos. No puede reutilizarse de inmediato en otro ensayo sin preparar nuevamente sus datos. |
| E2E-04: [rol-activo.spec.js](../e2e/tests/rol-activo.spec.js) | 2: elegir comite; no ofrecer administrador. | `autor.valencia@prueba2.2.com` con autor y comite, sin administrador. | Emite tokens y guarda rol activo en el navegador. No modifica los roles asignados. |
| E2E-05: [postular-articulo.spec.js](../e2e/tests/postular-articulo.spec.js) | 2: postular con dos coautores y PDF; rechazar el correo del responsable repetido como coautor. | Autor de `E2E_CORREO`, por defecto `autor.jose@prueba.com`; conferencia activa con plazo de postulacion abierto; linea `sistemas_software`; PDF generado en memoria. | El caso satisfactorio crea articulo, tres registros de autoria y version PDF. El caso negativo exige que no se cree el articulo. |
| E2E-06: [subir-pdf.spec.js](../e2e/tests/subir-pdf.spec.js) | 3: mostrar fecha de entrega del PDF; rechazar texto y completar con PDF valido; rechazar mas de 10 MB sin crear articulo. | Mismo autor configurable de E2E-05; conferencia con postulacion abierta; linea `tecnologias_informatica`. Genera PDF, texto y PDF de mas de 11 MB en memoria. | Los dos primeros casos terminan creando articulo y PDF. En el caso de texto, el articulo existe antes de corregir el archivo. El caso de tamaño exige ausencia del articulo. |
| E2E-07: [registro-autonomo-autores.spec.js](../e2e/tests/registro-autonomo-autores.spec.js) | 2: registro de autor y regreso al login; correo ya registrado. | No requiere sesion previa; CAPTCHA disponible; `autor.miguel@prueba.com` debe existir para el negativo. | Crea un autor con correo variable; el registro dispara el servicio de bienvenida. |
| E2E-08: [actualizar-perfil.spec.js](../e2e/tests/actualizar-perfil.spec.js) | 2: guardar apellidos y telefono y comprobarlos tras recargar; rechazar apellidos vacios. | `autor.miguel@prueba.com`, un solo rol autor. | El positivo cambia el perfil. El negativo comprueba validacion HTML y ausencia de mensaje de exito. |
| E2E-09: [crear-usuario.spec.js](../e2e/tests/crear-usuario.spec.js) | 2: crear autor desde gestion de usuarios; rechazar correo duplicado. | `comite.cristian@prueba.com`, solo comite; correo nuevo para el positivo y el del comite para el negativo. | Crea un autor y dispara bienvenida. Aunque el titulo dice administracion, la cuenta usada tiene rol comite, permitido por el codigo. |
| E2E-10: [borrar-usuario.spec.js](../e2e/tests/borrar-usuario.spec.js) | 2: crear y borrar un usuario desechable; no ofrecer borrado del administrador y rechazar borrado de autor con articulos. | Comite anterior; al menos un administrador visible; `cristian.madero@correounivalle.edu.co` como responsable de algun articulo. | Crea y borra una cuenta temporal. Las cuentas protegidas deben permanecer. No depende del usuario creado por E2E-09. |
| E2E-11: [consultar-articulos.spec.js](../e2e/tests/consultar-articulos.spec.js) | 3: filtro de titulo como autor; filtros de titulo, autor, conferencia y estado como comite; autor no ve articulo ajeno. | Autor `juandavid@teste2e.com`, comite `juan.salazar.caicedo@correunivalle.edu.co`, sus variables de contraseña y el conjunto de articulos descrito mas adelante. Exige conferencia con ID `4`. | No cambia articulos. Requiere cantidades y titulos concretos; datos adicionales pueden alterar las aserciones. |
| E2E-12: [quitar-coautor.spec.js](../e2e/tests/quitar-coautor.spec.js) | 2: quitar coautor y comprobar ausencia tras recargar; no permitir quitar al responsable desde UI ni API. | Autor `juandavid@teste2e.com`, articulo propio `articulo2`, autoria del responsable y coautor `coautor2ede`; postulacion abierta. | Elimina el coautor. El archivo indica restauracion manual con un articulo de ID `14`; ese ID esta en el comentario de preparacion, no en el recorrido automatizado. |
| E2E-13: [editar-articulo.spec.js](../e2e/tests/editar-articulo.spec.js) | 2: editar titulo y resumen; ocultar Editar y bloquear formulario con plazo cerrado. | `autor.jose@prueba.com`; articulo propio `Articulo editable e2e` con postulacion abierta y `Articulo de prueba para e2e` con postulacion cerrada. | El positivo cambia el titulo y resumen sin restaurarlos. El selector parcial puede seguir coincidiendo, pero no garantiza un estado inicial reproducible. |
| E2E-14: [cerrar-sesion.spec.js](../e2e/tests/cerrar-sesion.spec.js) | 2: volver al login y borrar access; rechazar renovacion con refresh anterior y redirigir una pagina protegida. | `autor.jose@prueba.com`, un solo rol autor; API en `http://127.0.0.1:8000/api`; migraciones de blacklist aplicadas. | Invalida refresh y limpia sesion del navegador. El caso negativo prueba el refresh anterior; no demuestra revocacion inmediata del access anterior. |

## Casos previstos que no estan en main

| Grupo | Lo indicado por la guia | Precondiciones propuestas, aun sin contrastar con una prueba implementada |
| --- | --- | --- |
| E2E-01 | Crear conferencia y verla en la lista; rechazar fecha final anterior a la inicial. Archivo esperado: `crear-conferencia.spec.js`. | Gestor (administrador o comite, segun `PermisoEventos`), nombre identificable y fechas de inicio/fin validas. El positivo crea una conferencia. |
| E2E-02 | Configurar fechas limite; rechazar orden invalido. Archivo esperado: `fechas-limite.spec.js`. | Gestor, conferencia propia del ensayo y cuatro fechas: postulacion, revision, version corregida y version final, en orden estricto. El positivo cambia sus plazos. |

No se crearon sustitutos ni se retiraron estos casos del alcance. Se debe
revisar su implementacion cuando este disponible.

## Cuentas necesarias para preparar el entorno

Los identificadores siguientes describen las dependencias del codigo actual.
En CI se deben crear registros de prueba locales, no acceder a las cuentas
compartidas. No es necesario conocer sus contraseñas reales: la preparacion
del entorno puede establecer contraseñas ficticias y pasarlas a las pruebas.

| Cuenta o perfil | Roles necesarios | Usos |
| --- | --- | --- |
| `autor.valencia@prueba1.com` | Autor | Login satisfactorio. |
| `autor.valencia@prueba2.com` | Autor | Bloqueo; debe ser exclusiva de ese caso y restablecerse antes de cada intento del test. |
| `autor.valencia@prueba2.2.com` | Autor y comite | Seleccion de rol, sin administrador. |
| `autor.jose@prueba.com` | Autor | Postulacion, PDF, edicion y cierre de sesion. |
| `autor.miguel@prueba.com` | Autor | Perfil y correo duplicado en registro. |
| `comite.cristian@prueba.com` | Comite | Creacion y borrado de usuarios. |
| `juandavid@teste2e.com` | Autor | Consulta y eliminacion de coautor. |
| `juan.salazar.caicedo@correunivalle.edu.co` | Comite | Filtros globales de articulos. Conservar el identificador exacto mientras no se parametrice la prueba. |
| `cristian.madero@correounivalle.edu.co` | Autor responsable de un articulo | Rechazo de eliminacion. No se inicia sesion con esta cuenta. |
| Un administrador | Administrador | Debe aparecer al filtrar usuarios y no ofrecer el boton Borrar. No requiere correo concreto en el test actual. |

Variables consumidas por los tests:

- `E2E_CORREO` y `E2E_PASSWORD`: opcionales en postulacion y PDF; tienen
  valores por defecto en esos archivos.
- `E2E_AUTOR_PASSWORD`: obligatoria en consulta y eliminacion de coautor.
- `E2E_COMITE_PASSWORD`: obligatoria en consulta como comite.
- Los demas archivos usan credenciales fijas. Parametrizarlas o hacerlas
  coincidir con los datos locales sera parte de la adaptacion posterior.

## Conferencias, articulos, autoria y fechas

La propiedad [Evento.postulacion_abierta](../backend/apps/eventos/models.py)
requiere conferencia activa y una `FechaLimite` de postulacion no vencida.
No basta crear la conferencia con fechas de inicio y fin futuras.

Se necesita al menos una conferencia abierta para postular, subir PDF, editar
y quitar coautores, y otra con postulacion cerrada para el negativo de edicion.
Las fechas deben calcularse respecto al momento de preparacion, con margen
suficiente para toda la ejecucion. Las fechas fijas terminaran venciendo.
Si se preparan las cuatro etapas mediante API, deben respetar el orden que
valida [FechasLimiteSerializer](../backend/apps/eventos/serializers.py).

| Articulo o relacion | Condicion que exige el codigo actual |
| --- | --- |
| `articulo2` | Responsable `juandavid@teste2e.com`, autor registrado con nombre `Juan David Salazar`, conferencia ID `4`, activo y con postulacion abierta para quitar coautor. Solo un resultado debe coincidir con ese titulo en el filtro. |
| `estamos melos` | Mismo autor visible y misma conferencia ID `4`; aparece al limpiar el filtro de titulo y no coincide con la palabra `articulo`. |
| `Articulo 1` y `Articulo sobre IA de prueba` | Visibles al comite, estado `en_revision`, coinciden con la palabra `articulo`. La prueba no requiere evaluaciones reales para verificar esos filtros. |
| `Prueba Jose` | Articulo activo de otro responsable, no de `juandavid@teste2e.com`. Debe existir en la preparacion: su ausencia en la tabla del autor por si sola podria pasar aunque el articulo no existiera. |
| `coautor2ede` | Registro de autoria de `articulo2`, correo `coautor2ede@prueba.com`, afiliacion `univalle`; debe existir al inicio de cada ejecucion del positivo de eliminacion. |
| Responsable de `articulo2` | Ademas de `autor_responsable`, debe existir su registro en `Articulo.autores`, con correo del responsable, para comprobar que no se puede quitar. |
| `Articulo editable e2e` | Responsable `autor.jose@prueba.com`; conferencia abierta; estado inicial de titulo/resumen restaurado antes del caso. |
| `Articulo de prueba para e2e` | Mismo responsable, conferencia cerrada. |
| Articulo del autor protegido frente a borrado | Responsable `cristian.madero@correounivalle.edu.co`. El comentario menciona `El avance de la IA`, pero ninguna asercion exige ese titulo. |

El filtro de autor consulta `articulo.autores.nombre`, no solo los nombres del
usuario. La preparacion debe crear esas relaciones de autoria. Los articulos
nuevos de postulacion y PDF se deben crear mediante el recorrido de UI, no
prepararse de antemano sustituyendo la operacion que la prueba verifica.

Es preferible que las adaptaciones identifiquen la conferencia y el articulo
por datos de prueba estables o por los IDs devueltos al prepararlos, en lugar
de depender de IDs de Supabase. No se han cambiado los selectores en esta etapa.

## Archivos y servicios

- Los archivos de E2E-05 y E2E-06 se construyen con `Buffer`; no dependen de
  PDF existentes en la computadora. Incluyen un PDF con cabecera `%PDF-`, un
  archivo de texto y un PDF con mas de 11 MB para superar el limite de 10 MB.
  El backend verifica extension, cabecera y tamaño, no la representacion visual
  completa del documento. No se necesita instalar un visor PDF para esos casos.
- La configuracion habitual utiliza PostgreSQL y almacenamiento S3 de
  Supabase. El entorno de CI debe disponer de base y archivos propios,
  descartables, sin credenciales de esos recursos compartidos.
- `settings_test.py` esta pensado para el ejecutor de pruebas de Django, con
  SQLite en memoria. No proporciona por si solo la base migrada y poblada que
  necesita un servidor E2E iniciado como proceso independiente. La preparacion
  posterior usa PostgreSQL con `settings_e2e`; los tests del backend en CI usan
  `settings_ci`. Ver [entorno de pruebas](entorno-e2e.md).
- Los recorridos cargan el iframe de reCAPTCHA y el backend consulta Google.
  Las claves de prueba facilitan el CAPTCHA, pero conservan la dependencia de
  red. La estrategia para CI queda por definir: cualquier simulacion debe
  limitarse al servicio externo, documentarse y quedar aislada del entorno
  habitual, conservando login, bloqueo y operaciones de negocio reales.
- Registro y creacion de usuarios llaman al correo de bienvenida. Configurar
  correo local de pruebas para evitar SMTP externo; el resultado de estas E2E
  no depende de recibir un mensaje en una cuenta real.

Fuentes: [settings.py](../backend/config/settings.py),
[settings_test.py](../backend/config/settings_test.py),
[servicios de usuarios](../backend/apps/usuarios/services.py) y
[validacion de articulos y PDF](../backend/apps/articulos/serializers.py).

## Configuracion y evidencias actuales

[playwright.config.js](../e2e/playwright.config.js) utiliza Chromium y
`http://localhost:5173` como URL base. `webServer` esta comentado: hoy hay que
iniciar backend y frontend por separado. E2E-11 y parte de E2E-12 tienen URLs
absolutas de frontend; E2E-12 y E2E-14 llaman tambien a la API en
`http://127.0.0.1:8000/api`. Cambiar solo `baseURL` no cambia todas esas rutas.
La URL de API del frontend se configura con `VITE_API_URL`.

La configuracion permite paralelismo local y usa un worker con `CI` definido.
Configura dos reintentos en CI, salvo login/bloqueo y seleccion de rol, que
los desactivan. Un worker reduce simultaneidad, pero no restaura datos entre
casos ni entre reintentos. El entorno debera restablecer los datos mutables o
asignar recursos independientes a cada caso e intento; comenzar con una base
limpia solo al inicio del job no resuelve todos esos cambios.

Se genera reporte HTML. Todos los archivos guardan capturas manuales con
nombres fijos en `evidencias/`, que se reemplazan al repetir la captura.
Postulacion y PDF tambien las adjuntan al reporte. Login y rol configuran
capturas automaticas cuando fallan. Las trazas se generan al primer reintento,
salvo consulta de articulos, que las desactiva. Con cero reintentos no se genera
una traza por esa opcion. Una captura manual posterior a una asercion no se
alcanza si la asercion falla antes.

El [workflow](../.github/workflows/ci.yml) incorpora ahora un servicio PostgreSQL
y un job E2E que instala Chromium y ejecuta las copias aisladas. Playwright
inicia la API y el frontend. La publicacion de reportes y evidencias como artifacts
esta configurada; su descarga real en GitHub queda pendiente de validacion.
`e2e/package.json` no define scripts de prueba; se utiliza la CLI de Playwright.

## Bloqueos y decisiones para las siguientes subtareas

1. Confirmar la disponibilidad de E2E-01 y E2E-02. No declarar cubierto todo el
   reparto del equipo con solo los 26 casos encontrados.
2. Preparar cuentas, conferencias, plazos, articulos y autoria locales. No usar
   esperas de 15 minutos ni restauracion manual del coautor.
3. Aislar base, almacenamiento y correo; definir el tratamiento de CAPTCHA.
   No simular la API del proyecto para hacer pasar los recorridos.
4. Parametrizar credenciales y rutas, y sustituir dependencias de IDs fijos.
   Conservar las aserciones funcionales existentes. Verificar que existe el
   articulo ajeno usado en la prueba de visibilidad negativa.
5. Gestionar contaminacion entre casos: bloqueo de cuenta, coautor eliminado,
   perfil modificado, titulo editado, articulos/usuarios acumulados y blacklist.
   Los sufijos con `Date.now()` evitan algunos duplicados, pero no limpian datos.
6. Iniciar servidores con espera de disponibilidad, ejecutar Chromium y guardar
   reporte/evidencias tanto si pasan como si fallan las pruebas.
7. Ejecutar dos veces desde datos nuevos y comprobar un fallo controlado antes
   de dar por completada la incorporacion de E2E a CI.

## Verificacion realizada

Con Playwright ya instalado, desde `e2e/` se ejecuto:

```bash
./node_modules/.bin/playwright test --list --reporter=list
```

Resultado: `Total: 26 tests in 12 files`, salida cero. Este comando verifica
el descubrimiento y la carga de los archivos sin abrir el navegador ni ejecutar
sus pasos. No demuestra que Chromium este instalado ni que los casos pasen.

No se instalaron dependencias, no se iniciaron servidores y no se modificaron
datos compartidos. Se revisaron los archivos de prueba, la guia del equipo,
la configuracion y las reglas de backend relacionadas. La unica incorporacion
del inventario fue este documento. La preparacion local se incorporo despues
y se describe en su guia. El workflow comprueba esa preparacion. Los casos
se adaptaron despues; su ejecucion con navegador en CI sigue pendiente.
