# Conecta

Proyecto de la materia Desarrollo de Software 1.

Aplicación web con una **API REST en Django** y un **frontend en React**, con la base de datos PostgreSQL alojada en **Supabase**.

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Django 6.1, Django REST Framework, Simple JWT, django-cors-headers |
| Base de datos | PostgreSQL en Supabase |
| Frontend | React 19 + Vite (JavaScript) |
| Peticiones HTTP | axios |
| Navegación | React Router |
| Gráficos | ApexCharts (react-apexcharts) |
| Almacenamiento de archivos | Supabase Storage (protocolo S3) con django-storages y boto3 |
| Seguridad del login | Google reCAPTCHA v2 |

## Estructura del repositorio

```
DesarrolloSoftware1/
├── backend/
│   ├── apps/              Módulos del proyecto (una app de Django por módulo)
│   ├── config/            Configuración general (settings.py, urls.py)
│   ├── .env.example       Plantilla de variables de entorno
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           axios.js y un archivo <modulo>Api.js por módulo
│   │   ├── components/    Componentes generales reutilizables
│   │   ├── pages/         Una carpeta por pantalla (<Nombre>Page.jsx + components/)
│   │   └── App.jsx        Rutas
│   ├── .env.example
│   └── package.json
└── README.md
```

## Requisitos

- [Python](https://www.python.org/downloads/) 3.11 o superior (al instalarlo, marca **Add Python to PATH**)
- [Node.js](https://nodejs.org/) 20 LTS o superior
- [Git](https://git-scm.com/)

## Instalación

Los comandos son para PowerShell en Windows.

### 1. Clonar el repositorio

```powershell
git clone https://github.com/jose-vanegas22/DesarrolloSoftware1.git
cd DesarrolloSoftware1
```

### 2. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Abre `backend/.env` y completa los valores:

- `DB_USER`, `DB_PASSWORD` y `DB_HOST`: pídeselos al responsable del proyecto por un medio privado.
- `SUPABASE_S3_ENDPOINT`, `SUPABASE_S3_REGION`, `SUPABASE_S3_ACCESS_KEY_ID` y `SUPABASE_S3_SECRET_ACCESS_KEY`: credenciales del bucket donde se guardan los PDF de los artículos. Pídeselas al responsable del proyecto por un medio privado. `SUPABASE_S3_BUCKET` ya viene con el valor `articulos`.
- `RECAPTCHA_SECRET_KEY`: para desarrollo usa la clave de prueba de Google `6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe`.
- `SECRET_KEY`: genera una propia con:

  ```powershell
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

Luego aplica las migraciones:

```powershell
python manage.py migrate
```

> Si PowerShell dice que la ejecución de scripts está deshabilitada al activar el venv, ejecuta una sola vez
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` y vuelve a intentarlo.

### 3. Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

## Ejecutar el proyecto

Se necesitan dos terminales al mismo tiempo.

**Terminal 1: backend** (API en http://127.0.0.1:8000)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

**Terminal 2: frontend** (aplicación en http://localhost:5173)

```powershell
cd frontend
npm run dev
```

Para iniciar sesión necesitas un usuario. Puedes crear uno con:

```powershell
python manage.py createsuperuser
```

La documentación interactiva de la API está en http://127.0.0.1:8000/api/docs/ (Swagger).


## Endpoints publicos

| Método | URL | Descripción |
|---|---|---|
| POST | `/api/token/` | Recibe `correo`, `password` y `captcha` (token de reCAPTCHA) y devuelve los tokens `access` y `refresh`. Tras 5 intentos fallidos, la cuenta se bloquea 15 minutos. |
| POST | `/api/token/refresh/` | Recibe `refresh` y devuelve un `access` nuevo |
| POST | `/api/usuarios/registro/` | Registro público de autores. Recibe `correo`, `password`, `nombres`, `apellidos`, `telefono` y `captcha` |
| POST | `/api/token/blacklist/` | Cierra la sesión: recibe `refresh` y lo invalida, para que ya no sirva para obtener nuevos tokens |



El token `access` dura 15 minutos y el `refresh` 120 minutos. Los demás endpoints requieren el header `Authorization: Bearer <access>`.

### Rol activo

Un usuario puede tener varios roles (administrador, comité, autor), pero en cada sesión trabaja con uno solo: el **rol activo**, que viaja dentro del token JWT. **Los permisos dependen del rol activo.**

- Si el usuario tiene **un solo rol**, el login lo deja como rol activo automáticamente.
- Si tiene **varios**, el login responde `"rol_activo": null` y debe elegir uno con `POST /api/usuarios/seleccionar-rol/` (`{ "rol": "comite" }`). Esa respuesta trae tokens nuevos, que reemplazan a los anteriores.

En el backend, el rol activo se obtiene con `obtener_rol_activo(request)` de `apps/usuarios/permissions.py`.

## Convenciones

- **Idioma:** lo que es del negocio va en español (`Producto`, `cargarProductos`, `/api/productos/`); lo técnico del framework queda en inglés (`models.py`, `ProductoSerializer`, `ProductosPage`, `getProductos`). En el código no se usan tildes ni ñ.
- **Backend:** cada módulo es una app dentro de `backend/apps/`, registrada en `INSTALLED_APPS` como `apps.<modulo>`.
- **Base de datos:** las tablas se crean solo desde los modelos de Django (`makemigrations` + `migrate`), nunca desde Supabase. Como todos usamos la misma base de datos, avisa al grupo antes de aplicar migraciones nuevas.
- **Frontend:** las páginas y componentes no usan axios directamente; llaman a funciones de `src/api/<modulo>Api.js`.
- **Archivos `.env`:** nunca se suben a Git. Si agregas una variable nueva, agrégala también al `.env.example`.
- **Swagger:** cada endpoint lleva `summary` (qué hace) y `description` (quién puede usarlo y reglas importantes) con `extend_schema`.


## Flujo de trabajo con Git

1. Actualiza `main` y crea una rama por HU:

   ```powershell
   git switch main
   git pull
   git switch -c feature/SCRUM-XX-nombre-corto
   ```

2. Haz commits con la clave de Jira al inicio: `SCRUM-XX Agrega ...`
3. Sube tu rama y crea un pull request hacia `main`.
4. Nunca trabajes directamente sobre `main`.

## Después de hacer `git pull`

| Si cambió... | Ejecuta |
|---|---|
| `backend/requirements.txt` | `pip install -r requirements.txt` |
| `frontend/package.json` | `npm install` |
| Alguna carpeta `migrations/` | `python manage.py migrate` |
| Algún `.env.example` | Agrega a tu `.env` las variables nuevas |
