# Pruebas de acceso

Revision del 23 de noviembre de 2026 sobre el codigo integrado en `main`
(commit `d8c4b84`). Se revisaron autenticacion, CAPTCHA, bloqueo por intentos
fallidos y seleccion del rol activo. Se conserva el inventario inicial y se
documentan las pruebas añadidas en esta rama, su estructura y sus resultados.

## Resultado de la revision inicial

Las 82 pruebas preexistentes del backend pasaron. Todas las clases encontradas
en esa revision heredaban de `APITestCase` y utilizaban base de datos; eran pruebas de
API/integracion, incluidas algunas comprobaciones directas de servicios con ORM.
No se encontraron pruebas unitarias aisladas de las funciones de permisos de
acceso, ni pruebas del backend que llamaran a los endpoints de login y seleccion
de rol. Las incorporaciones descritas mas adelante cubren esas carencias.
No se midio un porcentaje de cobertura de lineas.

Hay pruebas E2E de estos recorridos, pero no sustituyen las comprobaciones
aisladas del backend: utilizan navegador, cuentas compartidas y reCAPTCHA.
Se leyo su codigo; no se ejecutaron durante esta revision. El workflow actual
ejecuta las pruebas de Django, lint y build; todavia no ejecuta las E2E.

## Funcionalidad existente que se puede reutilizar

| Componente | Responsabilidad |
| --- | --- |
| [LoginSerializer](../backend/apps/usuarios/serializers.py) | Valida CAPTCHA, comprueba el bloqueo, autentica y devuelve tokens con el rol inicial. |
| [Configuracion de rutas](../backend/config/urls.py) | Expone `POST /api/token/`. |
| [SeleccionarRolSerializer y UsuarioViewSet](../backend/apps/usuarios/views.py) | La accion `POST /api/usuarios/seleccionar-rol/` exige autenticacion, valida un rol asignado y emite nuevos tokens. El serializer esta en `usuarios/serializers.py`. |
| [Usuario](../backend/apps/usuarios/models.py) | Guarda intentos fallidos y fecha de bloqueo; calcula `roles` y `rol_inicial`. |
| [Permisos de usuarios](../backend/apps/usuarios/permissions.py) | `obtener_rol_activo`, `es_gestor` y `es_administrador` comprueban el rol del token y su pertenencia al usuario. |
| [Servicio de CAPTCHA](../backend/apps/usuarios/services.py) | Consulta Google y devuelve un resultado booleano. |
| [Configuracion de pruebas](../backend/config/settings_test.py) | Proporciona base SQLite y almacenamiento en memoria para las pruebas de Django. |

No fue necesario desarrollar nuevos enpoints para comprobar los casos pendientes.

## Inventario previo a los cambios

Esta tabla conserva el estado anterior a la implementacion. Los numeros
corresponden a metodos de prueba, no a cada iteracion de `subTest`.

| Archivo y clases | Cantidad | Cobertura relacionada y limite |
| --- | --- | --- |
| [articulos/tests.py](../backend/apps/articulos/tests.py): `EvaluacionArticuloTests`, `EditarArticuloTests`, `DeshabilitarArticuloTests`, `FiltroConferenciaTests` | 46 (20 + 13 + 10 + 3) | Comprueban reglas de articulos, incluyendo autenticacion y permisos por rol. Preparan la sesion con `force_authenticate` o tokens creados directamente; no prueban el login ni la seleccion del rol. |
| [test_asignar_revisores.py](../backend/apps/articulos/test_asignar_revisores.py): `AsignarRevisoresTests` | 18 | Incluye rechazo de autor, administrador y peticion sin sesion. Usa tokens preparados directamente. |
| [test_consultar_evaluaciones.py](../backend/apps/articulos/test_consultar_evaluaciones.py): `ConsultarEvaluacionesTests` | 9 | Comprueba acceso del autor a sus evaluaciones y rechazo de acceso ajeno, rol comite o ausencia de sesion. Usa tokens preparados directamente. |
| [test_especialidades.py](../backend/apps/usuarios/test_especialidades.py): `EspecialidadesUsuarioTests` | 9 | Comprueba asignacion de especialidades por administrador y restricciones del comite, entre otras reglas. Usa tokens preparados directamente. |
| [usuarios/tests.py](../backend/apps/usuarios/tests.py) y [eventos/tests.py](../backend/apps/eventos/tests.py) | 0 | Solo contienen la plantilla inicial, sin metodos de prueba. |
| [login-bloqueo.spec.js](../e2e/tests/login-bloqueo.spec.js) | 2 E2E | Login con reCAPTCHA y cinco contraseñas incorrectas seguidas de rechazo de la correcta. No comprueba CAPTCHA invalido, estado interno del contador ni vencimiento del bloqueo. |
| [rol-activo.spec.js](../e2e/tests/rol-activo.spec.js) | 2 E2E | Seleccion de comite por usuario multirrol y ausencia de la opcion administrador no asignada. Comprueba interfaz y `localStorage`, pero no el rechazo de una solicitud directa con rol no asignado ni los claims de ambos JWT. |

## Cobertura incorporada

Los casos siguientes ya estan implementados en
[usuarios/tests.py](../backend/apps/usuarios/tests.py): cuatro metodos unitarios
y nueve de integracion. Las variantes de roles, intentos y limites de tiempo
usan `subTest`, por lo que el numero de metodos no coincide con el numero de
combinaciones comprobadas. Se conservan las 82 pruebas anteriores.

| Caso | Tipo | Comprobacion implementada |
| --- | --- | --- |
| Rol activo valido | Unitaria | Cada rol asignado se reconoce; un usuario multirrol utiliza solo el rol activo indicado. |
| Rol ausente, desconocido o no asignado | Unitaria | `obtener_rol_activo` devuelve `None`; poseer otros roles no concede el rol solicitado. |
| Clasificacion del rol | Unitaria | `es_gestor` permite administrador y comite; `es_administrador` solo administrador. Ambas rechazan autor y ausencia de rol valido. |
| Login valido, con uno o varios roles | Integracion | HTTP 200, identidad y roles correctos; access y refresh validos con rol unico o `rol_activo: null` para multirrol. No basta comprobar los campos JSON. |
| CAPTCHA invalido | Integracion | HTTP 400, sin tokens y sin aumentar el contador de contraseñas fallidas. La validacion externa devuelve un resultado controlado. |
| Cinco contraseñas incorrectas | Integracion | Los primeros cuatro fallos no bloquean; el quinto establece un bloqueo de 15 minutos y reinicia el contador a cero. Respuesta 401 sin tokens. |
| Contraseña correcta durante el bloqueo | Integracion | HTTP 401, sin tokens; la cuenta sigue bloqueada y la fecha de bloqueo no se altera. |
| Vencimiento del bloqueo | Integracion | Con tiempo controlado, antes del limite sigue bloqueada; en el limite y despues permite login valido, elimina el bloqueo y deja el contador en cero. |
| Login correcto despues de fallos sin bloqueo | Integracion | Reinicia el contador y permite iniciar una nueva secuencia de intentos. |
| Seleccion de un rol asignado | Integracion | El endpoint devuelve HTTP 200 y nuevos access y refresh con el rol seleccionado y la identidad del mismo usuario. Probar los roles asignados del usuario multirrol. |
| Seleccion de un rol conocido pero no asignado | Integracion | Enviar directamente el rol al endpoint produce HTTP 400 y no entrega tokens. Ocultar el boton en el frontend no demuestra esta proteccion. |

En el codigo actual, el quinto fallo establece el bloqueo pero devuelve el
error de autenticacion habitual; el siguiente intento muestra el mensaje de
cuenta bloqueada. Las nuevas pruebas comprueban tambien la base de datos
para distinguir el momento en que comienza el bloqueo.

Casos complementarios a valorar al implementar: CAPTCHA ausente, usuario
inexistente o inactivo, rol desconocido y seleccion sin autenticacion. No se
declaran cubiertos ni se incorporan automaticamente otros modulos al alcance.

## Estructura e implementacion

`PermisosAccesoUnitariosTests` hereda de `SimpleTestCase`. Comprueba
`obtener_rol_activo`, `es_gestor` y `es_administrador` usando objetos sencillos
con los atributos de una peticion y un usuario. No crea usuarios en la base
de datos ni usa red. Django impide consultas a la base en esta clase. Estas
pruebas permiten localizar errores en una funcion concreta sin involucrar
rutas HTTP, JWT o persistencia.

`AccesoIntegracionTests` hereda de `APITestCase`. Recorre las rutas de login y
seleccion de rol con el cliente de pruebas de Django: no necesita arrancar
un servidor ni abrir un navegador. Usa serializers, contraseñas, JWT y base
de datos temporal. Las peticiones de seleccion llevan un access obtenido
mediante el login real; no se utiliza `force_authenticate`.

La clase de integracion se organiza asi:

- `setUpTestData` crea un autor y un usuario con roles de autor y comite en la
  base de pruebas. Ninguno pertenece a Supabase ni a cuentas compartidas.
- `setUp` sustituye `apps.usuarios.serializers.verificar_captcha` por una
  respuesta controlada. Normalmente devuelve `True`; el caso de CAPTCHA
  invalido devuelve `False`. `addCleanup` retira la sustitucion incluso si
  una prueba falla. No se llama a Google ni se requieren claves reales.
- `login` envia los datos al endpoint, sin sustituir la autenticacion.
- `assertSesionValida` comprueba estado HTTP, roles de la respuesta e identidad
  y rol activo en ambos tokens. `AccessToken` y `RefreshToken` verifican firma,
  vigencia y tipo antes de inspeccionar sus datos.
- `assertSinTokens` comprueba que los errores no entregan access ni refresh.
- Los casos temporales controlan `timezone.now` en el login. Se prueban un
  segundo antes del vencimiento, el instante exacto y un segundo despues,
  sin esperar quince minutos. Cada variante restablece su estado inicial.

Cada metodo prepara sus datos, ejecuta una operacion y comprueba su resultado.
`refresh_from_db` permite verificar lo que quedo guardado, no solo los valores
que conserva el objeto Python. Los tests son independientes y sus cambios de
base de datos no permanecen al terminar.

| Grupo | Metodos y resultado esperado |
| --- | --- |
| Permisos | `test_reconoce_solo_el_rol_activo_asignado`, `test_rechaza_rol_ausente_desconocido_o_no_asignado`, `test_gestor_exige_rol_activo_administrador_o_comite_asignado`, `test_administrador_exige_rol_activo_administrador_asignado`: aceptar solo permisos del rol activo asignado. |
| Login | `test_login_con_un_rol_emite_tokens_con_ese_rol`, `test_login_multirrol_emite_tokens_sin_rol_activo`: HTTP 200 y rol correcto en respuesta y ambos JWT. |
| CAPTCHA | `test_captcha_invalido_rechaza_login_sin_alterar_intentos`: HTTP 400, sin tokens ni cambios en el contador. |
| Bloqueo | `test_quinto_fallo_activa_bloqueo_de_quince_minutos`, `test_cuenta_bloqueada_rechaza_password_correcta`: HTTP 401 y estado persistido correcto. |
| Recuperacion | `test_login_respeta_el_limite_del_bloqueo_y_limpia_su_estado`, `test_login_correcto_reinicia_intentos_antes_del_bloqueo`: recuperar el acceso en el momento permitido y reiniciar los contadores. |
| Seleccion de rol | `test_seleccion_de_rol_asignado_emite_nuevos_tokens`, `test_seleccion_de_rol_no_asignado_rechaza_peticion_directa`: HTTP 200 con nuevos JWT para roles asignados o HTTP 400 sin tokens para un rol no asignado. |

Los comentarios de las clases relacionan las pruebas con los requisitos de
acceso. No se movieron ni duplicaron las pruebas de otras funcionalidades.
Estas pruebas verifican ademas estado interno, tokens y solicitudes que la interfaz no ofrece.

## Ejecucion y resultados

Desde `backend/`, con su entorno virtual:

```bash
python manage.py test --settings=config.settings_test --noinput --verbosity 2
```

Para ejecutar solo las nuevas pruebas:

```bash
python manage.py test apps.usuarios.tests --settings=config.settings_test --noinput --verbosity 2
```

Para comprobar solo las unitarias, sin crear base de datos de pruebas:

```bash
python manage.py test apps.usuarios.tests.PermisosAccesoUnitariosTests --settings=config.settings_test --noinput --verbosity 2
```

`--verbosity 2` muestra el resultado de cada metodo; las variantes de `subTest`
se detallan cuando fallan. `--noinput` evita preguntas interactivas. El resultado
esperado es `OK` y codigo de salida cero. Una asercion incumplida produce un
fallo, salida distinta de cero y un job de CI fallido.

Resultado local del 23 de noviembre de 2026:

- Ejecucion enfocada: 13 pruebas nuevas satisfactorias.
- Suite completa: 95 pruebas satisfactorias (82 previas y 13 nuevas), sin
  problemas en la comprobacion de Django; codigo de salida cero.
- La base temporal se elimino al terminar. Los resultados de esta version
  aun no se han comprobado en un runner de GitHub.

El comando general de pruebas descubre automaticamente las nuevas clases,
no fue necesario cambiar el workflow.

No se instalaron dependencias ni se modifico la logica de la aplicacion,
la configuracion de pruebas o el workflow. Estas pruebas
no verifican la disponibilidad real de Google ni comportamientos exclusivos
de PostgreSQL; su objetivo es comprobar las reglas de acceso de forma aislada
de esos servicios.
