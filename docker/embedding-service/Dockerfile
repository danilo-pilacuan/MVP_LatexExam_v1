FROM python:3.11-slim

WORKDIR /app

# Instalar SOLO torch CPU primero (evita descargar cientos de MB de CUDA).
# Luego sentence-transformers con sus dependencias normales: como torch ya
# está instalado, pip no lo reinstalará con CUDA.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
        fastapi \
        uvicorn \
        sentence-transformers

COPY app.py /app/app.py

EXPOSE 8081

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8081"]
