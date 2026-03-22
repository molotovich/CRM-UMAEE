# ---- Build Stage ----
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para PyMySQL y cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Puerto que expone el contenedor (Cloud Run usa 8080 por defecto)
EXPOSE 8080

# Arrancar con Gunicorn apuntando al factory create_app()
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "120", "backend:create_app()"]
