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

La consulta `GET /api/students/c8a7d7de-5f33-4dd3-bfa7-dc1d675f7d34` devolvió `200` con los datos de Ana: [captura de la respuesta](evidencia/06-get-estudiante-200.png).

El cambio de edad de Ana mediante PATCH /api/students/{studentId} devolvió 200 y ge: 23: [captura de la respuesta](evidencia/07-patch-estudiante-200.png). Un GET posterior devolvió 200 y mantuvo ge: 23: [captura de la lectura](evidencia/08-get-edad-actualizada-200.png).

Un POST /api/students con el correo de Ana y otro username devolvió 409 con rrors.email: [captura del conflicto](evidencia/09-email-duplicado-409.png).

Un POST /api/students con ge: 10 devolvió 400 con rrors.age y el mensaje de edad mínima: [captura de validación](evidencia/10-edad-invalida-400.png).

Un GET /api/students/00000000-0000-0000-0000-000000000000 devolvió 404 con Estudiante no encontrado: [captura del recurso inexistente](evidencia/11-estudiante-inexistente-404.png).

Un POST /api/students/{studentId}/pets intentando crear otra Luna para Ana devolvió 409 con rrors.name: [captura del conflicto](evidencia/12-mascota-duplicada-409.png).

Se creó una segunda mascota de Ana, scubi du, mediante POST. La API devolvió 201 y el ID 454c986f-856f-4eb6-967a-c546908e7fe2: [captura de creación](evidencia/13-segunda-mascota-201.png).

El DELETE de scubi du devolvió 200 y el ID esperado: [captura de eliminación](evidencia/14-delete-mascota-200.png). Un GET posterior devolvió 	otal: 1 y solo a Luna: [captura de la lista](evidencia/15-lista-mascotas-tras-delete.png).

## Persistencia tras reiniciar contenedores

Se ejecutaron:

```powershell
docker compose down
docker compose up -d db adminer api
docker compose ps
```

Los tres servicios volvieron a quedar `Up`: [captura de la terminal](evidencia/03-reinicio-compose.png). El usuario confirmó que Ana y Luna seguían guardadas tras el reinicio. La fila de Ana se ve en [esta captura de `students`](evidencia/04-ana-tras-reinicio.png). La fila de Luna y su `studentId` se ven en [esta captura de `pets`](evidencia/05-luna-tras-reinicio.png). El comando usado fue `down` sin `-v`, por lo que se conservó el volumen de PostgreSQL.

## Colección Postman

Importar `postman/students-collection.json` y ejecutar las carpetas `01 - Students`, `02 - Pets` y `03 - Errors` en ese orden. La creación del estudiante genera un username y correo únicos y guarda automáticamente los IDs usados en las peticiones siguientes. La carpeta `04 - Final integration` borra al estudiante creado por la colección y debe ejecutarse solamente después de integrar Alembic, la clave foránea y el borrado transaccional. No usar los IDs de las capturas anteriores como variables de la colección.

## Pendiente de validar

Faltan capturas o resultados registrados para el borrado conjunto del estudiante con sus mascotas y el rollback. El esquema actual fue creado por `init_db()` al iniciar la API; aún no demuestra migraciones versionadas ni una clave foránea real de `pets.studentId` a `students.id`.

Para la entrega final, repetir las pruebas sobre el código integrado y una base nueva creada con Alembic. No usar `docker compose down -v` sobre datos que se quieran conservar.
