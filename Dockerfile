# -- BULD --
FROM python:3.13-slim-bookworm AS build

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv

# Lugar donde uv creará el entorno de Python
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Copiar los archivos de dependencias a directorio definido por WORKDIR = /app
COPY pyproject.toml uv.lock ./

# Instalar dependencias respetando uv.lock, sin instalar el proyecto
RUN uv sync --locked --no-install-project

# -- DEV --
# Crea una etapa llamada dev usando todo lo de build
FROM build AS dev

# Agrega los programas del entorno Python al PATH existente
ENV PATH="/opt/venv/bin:$PATH"

# Copia la carpeta app del proyecto a /app/app
COPY app ./app

# Copia la carpeta public del proyecto a /app/public
COPY public ./public

# Crea carpeta para base de datos
RUN mkdir -p /data

# Declara el puerto que utilizará la API
EXPOSE 3000

# Arranca el servidor en modo desarrollo
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]
