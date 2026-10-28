# CRUD Students & Pets (FastAPI)

Proyecto FastAPI que implementa un **CRUD** de estudiantes y mascotas con persistencia en PostgreSQL mediante SQLAlchemy. PostgreSQL, Adminer y la API se ejecutan con Docker Compose. Alembic gestiona la creación y los cambios del esquema.

## Tecnologías

- Python 3.13
- FastAPI + SQLAlchemy + PostgreSQL + Alembic
- Docker Compose (PostgreSQL 18, Adminer y API)
- HTML + JS + Tailwind CSS (frontend estático)

## Resumen funcional

La API expone operaciones CRUD completas sobre estudiantes y mascotas:

**Estudiantes** — `/api/students`

- **Crear**: `POST /api/students`
- **Listar**: `GET /api/students`
- **Buscar por id**: `GET /api/students/:id`
- **Actualizar**: `PATCH /api/students/:id`
- **Eliminar**: `DELETE /api/students/:id` (elimina también sus mascotas en una transacción)

**Mascotas** — `/api/students/:studentId/pets`

- **Listar**: `GET /api/students/:studentId/pets`
- **Crear**: `POST /api/students/:studentId/pets`
- **Actualizar**: `PATCH /api/students/:studentId/pets/:petId`
- **Eliminar**: `DELETE /api/students/:studentId/pets/:petId`

### Modelo de datos

| Estudiante | Mascota        |
| ---------- | -------------- |
| id (UUID)  | id (UUID)      |
| name       | studentId      |
| username   | name           |
| email      | species        |
| age        | age (opcional) |
| createdAt  | createdAt      |
| updatedAt  | updatedAt      |

### Validación y unicidad

La validación se realiza con Pydantic v2:

- `name` (estudiante): texto de 3 a 100 caracteres, sin etiquetas HTML.
- `username`: texto de 3 a 30 caracteres, solo minúsculas, números y guiones bajos (`^[a-z0-9_]+$`).
- `email`: dirección de correo electrónico válida.
- `age` (estudiante): entero entre 18 y 99.
- `name` / `species` (mascota): texto de 1 a 50 caracteres, sin etiquetas HTML.
- `age` (mascota): entero entre 0 y 100 (opcional).

Unicidad (rechazado con `409 Conflict`):

- Estudiante: `email` y `username` deben ser únicos.
- Mascota: `name` debe ser único dentro de un mismo estudiante.

## Estándar de respuesta JSON

Toda respuesta de la API — exitosa o de error — usa el mismo **envelope** `ApiResponse`, definido en [`app/shared/api_response.py`](app/shared/api_response.py). Esto permite que el frontend interprete cualquier respuesta de forma uniforme.

### Envelope común

| Campo       | Tipo                | Descripción                                                               |
| ----------- | ------------------- | ------------------------------------------------------------------------- |
| `code`      | `number`            | Código de estado HTTP (coincide con el status de la respuesta).           |
| `success`   | `boolean`           | `true` si la operación se completó, `false` si hubo error.                |
| `message`   | `string`            | Resumen legible del resultado (varía según el método HTTP).               |
| `timestamp` | `string`            | Fecha/hora en ISO 8601 de la respuesta.                                   |
| `data`      | `object \| null`    | Datos de la operación. Presente en éxito; `null` en errores.              |
| `error`     | `string` (opcional) | Mensaje de error para errores simples (404, 500).                         |
| `errors`    | `object` (opcional) | Errores por campo para validación (400) y conflicto (409). Ver más abajo. |

### Respuestas de éxito

Un middleware global ([`api_response.py`](app/shared/api_response.py)) envuelve el retorno de los controladores en `data`:

- **Recurso único** (`GET :id`, `POST`, `PATCH`, `DELETE`): `data` contiene la entidad directamente.
- **Listado** (`GET` colección): `data` contiene `{ total, items }`.

```json
{
  "code": 201,
  "success": true,
  "message": "Recurso creado",
  "timestamp": "2026-09-09T16:49:33.368Z",
  "data": {
    "id": "c3600646-abe8-4be3-8096-d6ad629388e2",
    "name": "Juan Pérez",
    "username": "juanperez",
    "email": "juan@example.com",
    "age": 20,
    "createdAt": "2026-09-09T16:49:33.000Z",
    "updatedAt": "2026-09-09T16:49:33.000Z"
  }
}
```

`message` según el método HTTP:

| Método   | `message`             | `code` |
| -------- | --------------------- | ------ |
| `GET`    | `Operación exitosa`   | 200    |
| `POST`   | `Recurso creado`      | 201    |
| `PATCH`  | `Recurso actualizado` | 200    |
| `DELETE` | `Recurso eliminado`   | 200    |

### Errores simples (404, 500)

Los errores sin detalle por campo usan el campo `error`:

```json
{
  "code": 404,
  "success": false,
  "message": "Estudiante no encontrado",
  "timestamp": "2026-09-09T16:49:53.816Z",
  "data": null,
  "error": "Estudiante no encontrado"
}
```

### Validación (400) y conflicto (409)

Ambos casos comparten el **mismo esquema** para que el frontend los trate igual: el campo `errors` es un mapa `{ campo: { message } }`, donde la clave es el nombre del campo que falla.

```json
{
  "code": 400,
  "success": false,
  "message": "Error de validación",
  "timestamp": "2026-09-09T16:39:30.397Z",
  "data": null,
  "errors": {
    "name": { "message": "El nombre debe tener entre 3 y 100 caracteres" },
    "email": { "message": "El correo electrónico no es válido" }
  }
}
```

```json
{
  "code": 409,
  "success": false,
  "message": "Conflicto con datos existentes",
  "timestamp": "2026-09-09T16:49:45.110Z",
  "data": null,
  "errors": {
    "email": { "message": "El correo electrónico ya está en uso" }
  }
}
```

- `400 Bad Request`: cuando falla la validación. Los DTOs usan mensajes en español; el handler global ([`exceptions.py`](app/shared/exceptions.py)) convierte los errores al mapa `{ campo: { message } }` (si un campo falla varias reglas, los mensajes se concatenan con `", "`; las propiedades no permitidas devuelven `errors: {}`).
- `409 Conflict`: cuando se viola una restricción de unicidad. Los servicios lanzan una `HTTPException` con el mismo mapa `errors`, por lo que es indistinguible de una validación a nivel de estructura.

### Interpretación en el frontend

El cliente estático (`public/`) consume este estándar de forma uniforme:

- `public/js/api.js` expone `api()` (hace `fetch` y devuelve `data` en éxito o lanza el envelope en error) y `normalizeErrors()` (convierte `{ campo: { message } }` en `{ campo: message }`).
- En los formularios, si la respuesta trae `errors`, cada mensaje se muestra bajo su input correspondiente; si trae `error`, se muestra como notificación global (toast).

## Contexto técnico

- **Backend**: FastAPI
- **Persistencia**: PostgreSQL con SQLAlchemy 2.0 y psycopg
- **Validación**: Pydantic v2
- **Frontend**: archivos estáticos en `public/` (Alpine.js + Tailwind CSS + vanilla-sonner, vía CDN)
- **Gestor de dependencias**: uv
- **Documentación**: Swagger en `/docs`

## Requisitos

- Docker Desktop con el motor de contenedores Linux funcionando (en Windows, con WSL 2).
- Python 3.13 y `uv` para ejecutar Alembic desde la máquina anfitriona.
- Puertos locales 3000, 5432 y 8080 disponibles.

## Primera puesta en marcha

Los ejemplos siguientes usan PowerShell desde la raíz del proyecto. En Linux o Ubuntu se usan los mismos comandos de Docker y `uv`; para copiar un archivo se usa `cp` en lugar de `Copy-Item`.

1. Preparar las variables locales. Copiar el ejemplo, editar `.env` y elegir una contraseña propia. No subir `.env` a Git:

    ```powershell
    Copy-Item .env.example .env
    notepad .env
    ```

    Las variables son `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`. Si el volumen de PostgreSQL ya estaba inicializado, cambiar usuario o contraseña en `.env` no cambia las credenciales guardadas en ese volumen.

2. Levantar la base y Adminer. Esperar en los logs a `database system is ready to accept connections`:

    ```powershell
    docker compose config --quiet
    docker compose up -d db adminer
    docker compose logs --tail=30 db
    ```

3. Instalar las dependencias locales y preparar una URL de migración en un archivo **local** `.env.alembic`:

    ```powershell
    uv sync
    notepad .env.alembic
    ```

    Ejemplo del contenido, usando el usuario, contraseña y base de `.env`:

    ```dotenv
    DATABASE_URL=postgresql+psycopg://taller:SU_CLAVE@localhost:5432/taller2
    ```

    `localhost:5432` es la dirección vista desde Windows o Ubuntu. La API dentro de Docker usa `db:5432`, configurado en `compose.yml`. Para simplificar la URL, usar una contraseña alfanumérica con guion bajo; otros caracteres deben codificarse en la URL. `.env.alembic` se mantiene fuera de Git.

4. Aplicar la migración **antes** de iniciar la API sobre una base vacía:

    ```powershell
    uv run --env-file .env.alembic alembic upgrade head
    uv run --env-file .env.alembic alembic current
    uv run --env-file .env.alembic alembic check
    ```

    `current` debe indicar la revisión `head` y `check` no debe detectar cambios pendientes. La migración crea `students`, `pets`, su clave foránea y `alembic_version`. La API no aplica migraciones automáticamente.

5. Levantar la API y comprobar los servicios:

    ```powershell
    docker compose up -d --build api
    docker compose ps
    ```

    API: `http://localhost:3000`; Swagger: `http://localhost:3000/docs`; Adminer: `http://localhost:8080`. En Adminer elegir PostgreSQL, servidor `db` y los datos de `.env`.

### Si la base ya tiene tablas

No ejecutar la migración inicial de creación sobre una base antigua que ya tenga `students` y `pets`: fallaría por tablas existentes. Tampoco usar `alembic stamp head` como atajo, porque no agrega la clave foránea. Crear otra base vacía desde Adminer, apuntar `POSTGRES_DB` y `.env.alembic` a ella, aplicar `upgrade head` y luego levantar la API. Los datos de la base anterior no se trasladan solos. Una migración de datos existentes requiere un procedimiento de transición aparte.

### Persistencia y pruebas manuales

`docker compose down` detiene los contenedores y conserva el volumen `pgdata`; `docker compose down -v` elimina ese volumen y sus datos. Para comprobar persistencia, crear un estudiante y una mascota, ejecutar `down` y luego `up -d`, y verificar que siguen presentes.

La colección [Postman](postman/students-collection.json) incluye CRUD y casos 400, 404 y 409. Genera IDs de prueba automáticamente. Su carpeta de integración final elimina un estudiante con mascota; usarla sobre una base de pruebas después de aplicar las migraciones.

El borrado de estudiante elimina primero sus mascotas y confirma ambos cambios en un solo `commit`; ante un error hace `rollback`. La rúbrica exige **verificar ese rollback ante un fallo**, por lo que la presencia del código no sustituye la prueba. Una prueba de integración debe forzar un error después del borrado de mascotas y comprobar en una nueva sesión que permanecen tanto el estudiante como sus mascotas.
