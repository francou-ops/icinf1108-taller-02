# Validación inicial de Docker y CRUD

Esta guía registra las comprobaciones realizadas en la base local `taller2`. No contiene credenciales. El archivo `.env` local debe definir `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`; no se versiona.

## Servicios y esquema

Desde la raíz del proyecto se ejecutaron:

```powershell
docker compose config --quiet
docker compose up -d db adminer
docker compose logs --tail=20 db
docker compose up -d --build api
docker compose ps
```

La configuración de Compose fue aceptada. PostgreSQL registró `database system is ready to accept connections`. Adminer abrió en `http://localhost:8080` con el servidor `db`. La API creó las tablas `students` y `pets` en `taller2`, visibles en Adminer: [captura del esquema](evidencia/01-tablas-postgresql.png). La API quedó disponible en `http://localhost:3000/docs`.

## Prueba de creación

Se creó el estudiante Ana mediante `POST /api/students`; la respuesta fue `201` y entregó el ID `c8a7d7de-5f33-4dd3-bfa7-dc1d675f7d34`. No se conservó captura de esa respuesta. El usuario verificó su registro en Adminer.

Se creó la mascota Luna mediante `POST /api/students/{studentId}/pets`, con ese ID de estudiante. La respuesta fue `201` y devolvió el ID `3465c52b-3dbb-4d09-b9d9-fb07b2c568cc`: [captura de la respuesta](evidencia/02-post-mascota-201.png).

## Persistencia tras reiniciar contenedores

Se ejecutaron:

```powershell
docker compose down
docker compose up -d db adminer api
docker compose ps
```

Los tres servicios volvieron a quedar `Up`: [captura de la terminal](evidencia/03-reinicio-compose.png). El usuario confirmó que Ana y Luna seguían guardadas tras el reinicio. La fila de Ana se ve en [esta captura de `students`](evidencia/04-ana-tras-reinicio.png). La fila de Luna y su `studentId` se ven en [esta captura de `pets`](evidencia/05-luna-tras-reinicio.png). El comando usado fue `down` sin `-v`, por lo que se conservó el volumen de PostgreSQL.

## Pendiente de validar

Faltan capturas o resultados registrados para GET, PATCH, DELETE, errores 400/404/409, borrado conjunto y rollback. El esquema actual fue creado por `init_db()` al iniciar la API; aún no demuestra migraciones versionadas ni una clave foránea real de `pets.studentId` a `students.id`.

Para la entrega final, repetir las pruebas sobre el código integrado y una base nueva creada con Alembic. No usar `docker compose down -v` sobre datos que se quieran conservar.


