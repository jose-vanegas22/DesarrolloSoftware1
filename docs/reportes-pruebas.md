# Reportes, evidencias y cobertura de pruebas

## Que es un artifact

Es un conjunto de archivos que GitHub guarda asociado a una ejecucion del
workflow; no es un commit, una rama ni una publicacion de la aplicacion.
`actions/upload-artifact` los copia desde el runner al almacenamiento de GitHub
antes de que termine el job, para poder descargarlos despues.

El workflow publica dos artifacts independientes:

| Nombre (prefijo) | Contenido | Retencion |
| --- | --- | --- |
| `cobertura-backend` | HTML navegable, XML, JSON, resumen de cobertura y log de tests Django. | 30 dias |
| `e2e-reportes` | Reporte HTML de Playwright, resultados JSON, capturas y trazas disponibles. | 30 dias |

Los nombres incluyen el numero de ejecucion y su intento para distinguirlos.
`if: always()` hace que se intente subir lo disponible aunque fallen las pruebas.
No hay `continue-on-error`: un test fallido sigue haciendo fallar el job.
El job backend usa Bash con `pipefail`, de modo que guardar el log con `tee`
no oculta el codigo de error del ejecutor de tests.

Si la instalacion o el arranque falla antes de generar archivos, la subida
avisa que no encontro resultados. Si el runner se pierde o la ejecucion se
termina abruptamente, la subida tampoco esta garantizada.
La conservacion durante 30 dias queda sujeta a los limites del repositorio.
Descargar los archivos antes de su vencimiento si se necesitan para el informe.

No se suben el `.env`, la base PostgreSQL, el directorio temporal de usuarios/PDF
ni credenciales de Supabase. Los recorridos utilizan cuentas ficticias; las
trazas pueden contener datos de esas cuentas y solicitudes de la aplicacion.

## Consultarlos en GitHub

1. Abrir el repositorio, **Actions**, el workflow **CI** y la ejecucion deseada.
2. Revisar el estado de cada job y sus logs. El resumen incluye la tabla de cobertura.
3. En **Artifacts**, descargar el archivo correspondiente y extraer el ZIP.
4. Para cobertura, abrir `html/index.html` dentro del contenido extraido.
5. Para E2E, desde un proyecto con Playwright instalado, ejecutar
   `npx playwright show-report /ruta/extraida/playwright-report`.
6. Una traza `.zip` se abre con `npx playwright show-trace /ruta/trace.zip`.

Conservar juntas las carpetas del reporte de Playwright y sus recursos.
Los artifacts requieren acceso a la ejecucion y normalmente sesion en GitHub;
no son un sitio web publico. No hay que hacer commit de los reportes.

## Que mide la cobertura

Coverage.py observa el codigo Python ejecutado durante los tests Django.

- **Lineas:** sentencias ejecutables que se alcanzaron.
- **Ramas:** caminos de salida de decisiones y otros saltos de control. Probar
  un `if` solo con un valor verdadero no recorre su alternativa.
- **Indicador combinado:** cuando se activan ramas, la columna `Cover` combina
  sentencias y caminos cubiertos. No debe citarse como porcentaje solo de lineas.

Ejecutar una linea no demuestra que exista una asercion correcta sobre ella.
El reporte ayuda a decidir donde añadir pruebas relevantes, no a perseguir un
numero aislado.

## Alcance de la medicion

`backend/.coveragerc` mide `backend/apps` con ramas activadas. Incluye modelos,
serializers, vistas, permisos, servicios y comandos de gestion. Omite las
migraciones y los archivos de tests, que no son el comportamiento que se quiere
medir. No excluye codigo de negocio para mejorar artificialmente el porcentaje.

No mide JavaScript/React, el directorio `config`, librerias externas ni las
lineas ejecutadas por los servidores E2E. El reporte de Playwright indica
**casos que pasan o fallan**, no cobertura de lineas. No se deben sumar ambos
indicadores ni presentar la cobertura del backend como cobertura del proyecto.

Por ese motivo los comandos `preparar_e2e` y `restablecer_e2e` aparecen con 0 %
en esta medicion aunque los recorridos E2E los utilicen en otro proceso.
CI no impone un umbral minimo de cobertura: los valores se registran como linea
base y el equipo puede acordar objetivos con pruebas de comportamiento.

## Generar cobertura localmente

Con un PostgreSQL exclusivo de pruebas iniciado como explica
[entorno-e2e.md](entorno-e2e.md), desde `backend/` y con el entorno virtual activo:

```bash
python -m pip install -r requirements-ci.txt
export CONECTA_TEST_DB_PORT=55432  # Puerto del ejemplo Docker de la guia.
mkdir -p reportes/cobertura
python -m coverage run manage.py test --settings=config.settings_ci --noinput --verbosity 2
python -m coverage report
python -m coverage html
python -m coverage xml
python -m coverage json
```

La dependencia de medicion esta fijada en `requirements-ci.txt`; las dependencias
habituales de la aplicacion siguen en `requirements.txt`. No hace falta instalar
coverage.py para usar el comando habitual `python manage.py test`.

El HTML queda en `backend/reportes/cobertura/html/index.html`; el JSON y XML
contienen los datos para otras herramientas. `coverage run` inicia una medicion
nueva; generar reportes despues de una suite fallida no la convierte en aprobada.
`backend/.gitignore` excluye los resultados.

## Evidencias de Playwright

Las copias CI generan HTML y `e2e/test-results/resultados.json`. Mantienen sus
capturas explicitas y añaden captura automatica ante un fallo. La configuracion
retiene trazas de los intentos fallidos, incluso el primero; no guarda trazas
de los que pasan. Los casos de consulta conservan su opcion especifica de
trazas desactivadas. No se graban videos.

Para ejecutar los recorridos como CI, preparar una base y carpeta nuevas con
`preparar_e2e`, exportar las mismas variables de conexion y `CONECTA_E2E_DIR`
en la terminal de Playwright y ejecutar desde `e2e/`:

```bash
CI=1 npx playwright test --config=playwright.ci.config.js
npx playwright show-report
```

No iniciar Django ni Vite manualmente: Playwright los administra. Las copias
estan en `tests-ci/`; los originales de `tests/` permanecen intactos. El detalle
de preparacion esta en [la guia del entorno](entorno-e2e.md).

Cada ejecucion local puede reemplazar resultados anteriores. En GitHub quedan
separados por ejecucion/intento hasta vencer la retencion.

## Linea base local del 23 de noviembre de 2026

### Cobertura del backend

Las 82 pruebas Django presentes en esta rama pasaron con PostgreSQL 18.7:

| Medida | Cubierto / total | Porcentaje |
| --- | --- | --- |
| Lineas ejecutables | 706 / 1053 | 67,05 % |
| Ramas | 111 / 254 | 43,70 % |
| Indicador combinado | 817 / 1307 | 62,51 % |

Estos valores corresponden exclusivamente a las pruebas presentes en esta rama.

Las zonas con menor cobertura incluyen servicios de usuarios y partes de
serializers y vistas de usuarios/eventos. El HTML muestra las lineas concretas
sin ejecutar.

### Recorridos E2E

Las 26 copias CI se ejecutaron sobre una base nueva: **26 aprobadas en
3,6 minutos, 0 fallidas, 0 omitidas y 0 inestables**. No hubo reintentos. Se
generaron el HTML, `resultados.json` y 35 capturas PNG. Al no fallar casos no
se conservaron trazas.
