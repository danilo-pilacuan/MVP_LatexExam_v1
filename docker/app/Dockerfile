FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Copiar requirements e instalar dependencias.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar el código de la aplicación (incluye alembic.ini para migraciones).
COPY main.py /app/main.py
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY alembic.ini /app/alembic.ini
COPY docker/app/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
