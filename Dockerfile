# Usar una imagen base oficial de Python ligera
FROM python:3.12-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL y compilación
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos e instalar dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . /app/

# Recopilar archivos estáticos (se ejecutará al construir o al iniciar, 
# pero es mejor aquí si no hay secretos necesarios para collectstatic, 
# o usar un script de entrada. Para Django a veces se necesita la DB o SECRET_KEY.
# Lo haremos en el comando de arranque o script de entrada si es necesario.
# Por ahora solo copiamos.)

# Exponer el puerto
EXPOSE 8000

# Comando por defecto (puede ser sobrescrito por docker-compose)
# Comando por defecto (puede ser sobrescrito por docker-compose)
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]
