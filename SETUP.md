# 🚀 Unidades Móviles SRT - Guía Completa

Sistema de gestión de unidades móviles con streaming WebRTC/WHEP sobre HTTPS.

---

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Git (para clonar el repositorio)
- Acceso a un servidor MediaMTX/vMix (opcional, para streaming)

---

## 🛠️ Instalación y Configuración Inicial

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd unidades_moviles
```

### 2. Configurar variables de entorno

El archivo `.env` ya contiene valores de desarrollo. Puedes editarlo si necesitas cambiar algo:

```bash
nano .env
```

**Configuración actual (desarrollo):**
- `DEBUG=True` - Modo desarrollo con logs detallados
- `CSRF_TRUSTED_ORIGINS=https://localhost,https://127.0.0.1` - Permite HTTPS local
- `VMIX_HOST=http://host.docker.internal:8889` - URL del servidor MediaMTX

### 3. Levantar el proyecto

```bash
# Construir las imágenes Docker
docker compose build

# Iniciar todos los servicios
docker compose up -d

# Ver los logs (opcional)
docker compose logs -f
```

### 4. Crear superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Acceder a la aplicación

- **Aplicación:** https://localhost
- **Panel Admin:** https://localhost/admin

> **Nota:** El navegador mostrará una advertencia de seguridad porque usamos certificados SSL autofirmados. Esto es normal en desarrollo. Haz clic en "Avanzado" y acepta el certificado.

---

## 💻 Desarrollo - Uso Diario

### Iniciar/Detener el proyecto

```bash
# Iniciar
docker compose up -d

# Detener (mantiene datos)
docker compose down

# Detener y eliminar TODO (incluyendo base de datos)
docker compose down -v
```

### Ver logs

```bash
# Todos los servicios
docker compose logs -f

# Un servicio específico
docker compose logs -f web
docker compose logs -f nginx
docker compose logs -f db
```

### Comandos Django frecuentes

```bash
# Crear/aplicar migraciones
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Crear superusuario
docker compose exec web python manage.py createsuperuser

# Shell de Django
docker compose exec web python manage.py shell

# Recolectar archivos estáticos
docker compose exec web python manage.py collectstatic --noinput
```

### Trabajar con archivos estáticos

Cuando agregues o modifiques CSS, JavaScript o imágenes en `core/static/`:

```bash
# 1. Agregar/modificar archivo
# Ejemplo: core/static/core/css/nuevo-estilo.css

# 2. Ejecutar collectstatic
docker compose exec web python manage.py collectstatic --noinput

# 3. Verificar que nginx lo tenga
docker compose exec nginx ls -la /app/static_root/
```

> **Importante:** `collectstatic` se ejecuta automáticamente al iniciar el contenedor, pero si agregas archivos mientras está corriendo, debes ejecutarlo manualmente.

### Reiniciar servicios

```bash
# Un servicio
docker compose restart web
docker compose restart nginx

# Todos
docker compose restart
```

### Base de datos

```bash
# Conectar a PostgreSQL
docker compose exec db psql -U postgres -d unidades_moviles

# Backup
docker compose exec db pg_dump -U postgres unidades_moviles > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260115.sql | docker compose exec -T db psql -U postgres unidades_moviles
```

---

## 🌐 Configuración HTTPS y WebRTC

### Certificados SSL

Los certificados SSL se generan automáticamente al iniciar nginx:

- **Ubicación:** `nginx/ssl/`
- **Archivos:** `localhost.crt` y `localhost.key`
- **Validez:** 365 días
- **Dominios:** localhost, *.localhost, 127.0.0.1

#### Regenerar certificados

```bash
rm nginx/ssl/localhost.crt nginx/ssl/localhost.key
docker compose restart nginx
```

### Proxy WHEP para MediaMTX

El sistema incluye un proxy WHEP que permite acceder a streams WebRTC a través de nginx.

**Formato de URL:**
```
https://localhost/usuario/movil1/whep
https://localhost/usuario/movil2/whep
```

**Configurar servidor MediaMTX:**

Edita `.env` y cambia `VMIX_HOST`:

```bash
# Servidor en tu máquina
VMIX_HOST=http://host.docker.internal:8889

# Servidor en red local
VMIX_HOST=http://192.168.1.50:8889

# Servidor remoto
VMIX_HOST=http://servidor.example.com:8889
```

Después de cambiar, reinicia:
```bash
docker compose restart
```

**Usar en JavaScript:**
```javascript
const whepUrl = 'https://localhost/usuario/movil1/whep';
// nginx se encarga del proxy, CORS y HTTPS
```

---

## 🏭 Despliegue en Producción

### 1. Preparar archivo de entorno

```bash
# Copiar template de producción
cp .env.production .env

# Editar valores
nano .env
```

**Cambios OBLIGATORIOS:**

```bash
# Seguridad
DEBUG=False
SECRET_KEY=GENERA-UNA-CLAVE-ALEATORIA-SEGURA-AQUI
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com

# Base de datos (usar contraseñas seguras)
DATABASE_NAME=unidades_moviles_prod
DATABASE_USER=unidades_moviles_user
DATABASE_PASSWORD=TU-CONTRASEÑA-SUPER-SEGURA

POSTGRES_DB=unidades_moviles_prod
POSTGRES_USER=unidades_moviles_user
POSTGRES_PASSWORD=LA-MISMA-CONTRASEÑA-DE-ARRIBA

# MediaMTX real
VMIX_HOST=http://tu-servidor-mediamtx.com:8889
```

**Generar SECRET_KEY seguro:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Obtener certificados SSL reales

**Opción A: Let's Encrypt (recomendado)**

```bash
# Instalar Certbot
sudo apt install certbot

# Generar certificados
sudo certbot certonly --standalone -d tudominio.com -d www.tudominio.com

# Copiar al proyecto
sudo cp /etc/letsencrypt/live/tudominio.com/fullchain.pem nginx/ssl/localhost.crt
sudo cp /etc/letsencrypt/live/tudominio.com/privkey.pem nginx/ssl/localhost.key
sudo chown $USER:$USER nginx/ssl/*
```

**Opción B: Certificados propios**

```bash
cp tu-certificado.crt nginx/ssl/localhost.crt
cp tu-llave-privada.key nginx/ssl/localhost.key
```

### 3. Actualizar nginx para producción

Edita `nginx/templates/default.conf.template`:

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name tudominio.com www.tudominio.com;  # Cambiar localhost por tu dominio
    # ... resto sin cambios
}

server {
    listen 80;
    server_name tudominio.com www.tudominio.com;  # Cambiar localhost
    return 301 https://$server_name$request_uri;
}
```

### 4. Configurar Gunicorn

Agregar a `requirements.txt`:
```
gunicorn==21.2.0
```

Crear `docker-compose.prod.yml`:

```yaml
services:
  web:
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - static_volume:/app/static_root
      - media_volume:/app/media_root
```

### 5. Desplegar

```bash
# 1. Subir código al servidor
git pull origin main

# 2. Construir
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# 3. Levantar
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Crear superusuario
docker compose exec web python manage.py createsuperuser

# 5. Verificar
docker compose logs -f
```

### 6. Checklist de seguridad

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` único y seguro (50+ caracteres)
- [ ] Contraseñas de BD seguras y únicas
- [ ] `ALLOWED_HOSTS` con tu dominio específico
- [ ] `CSRF_TRUSTED_ORIGINS` con URLs HTTPS
- [ ] Certificados SSL reales de Let's Encrypt
- [ ] `.env` en `.gitignore` (verificar)
- [ ] Firewall: solo puertos 80, 443, 22 abiertos
- [ ] Backups automáticos configurados
- [ ] Monitoreo de logs activo

---

## 🐛 Solución de Problemas

### Error: "CSRF verification failed"

```bash
# Verificar configuración
docker compose exec web python manage.py shell -c "from django.conf import settings; print(settings.CSRF_TRUSTED_ORIGINS)"

# Limpiar cookies del navegador y recargar la página
```

### Archivos estáticos no cargan (404)

```bash
# Ejecutar collectstatic
docker compose exec web python manage.py collectstatic --noinput

# Verificar que nginx tenga acceso
docker compose exec nginx ls -la /app/static_root/

# Ver logs
docker compose logs nginx | grep static
```

### No conecta a base de datos

```bash
# Ver estado
docker compose ps

# Logs de PostgreSQL
docker compose logs db

# Verificar variables
docker compose exec web env | grep DATABASE
```

### Certificados SSL no funcionan

```bash
# Verificar que existan
ls -la nginx/ssl/

# Regenerar (desarrollo)
rm nginx/ssl/localhost.*
docker compose restart nginx

# Ver logs de nginx
docker compose logs nginx | grep ssl
```

### WebRTC no funciona

- Asegúrate de usar **HTTPS** (WebRTC lo requiere)
- Verifica que `VMIX_HOST` en `.env` sea correcto
- Revisa los logs del proxy: `docker compose logs nginx | grep whep`
- Prueba acceder directamente al servidor MediaMTX

---

## 📚 Comandos Útiles

### Docker

```bash
# Estado de contenedores
docker compose ps

# Uso de recursos
docker stats

# Limpiar sistema
docker system prune -a

# Ver volúmenes
docker volume ls

# Inspeccionar volumen
docker volume inspect unidades_moviles_static_volume
```

### Django

```bash
# Crear nueva app
docker compose exec web python manage.py startapp nombre_app

# Ejecutar tests
docker compose exec web python manage.py test

# Verificar configuración
docker compose exec web python manage.py check

# Ver URLs
docker compose exec web python manage.py show_urls
```

---

## 🔄 Actualizar el Proyecto

```bash
# 1. Obtener cambios
git pull origin main

# 2. Reconstruir (si hubo cambios en Dockerfile)
docker compose build

# 3. Aplicar migraciones
docker compose exec web python manage.py migrate

# 4. Recolectar estáticos
docker compose exec web python manage.py collectstatic --noinput

# 5. Reiniciar
docker compose restart
```

---

## 📁 Estructura del Proyecto

```
unidades_moviles/
├── .env                    # Variables de entorno (NO subir a git)
├── .env.example            # Template de configuración
├── .env.production         # Template para producción
├── docker-compose.yml      # Configuración Docker
├── Dockerfile              # Imagen Django
├── entrypoint.sh           # Script de inicio (migraciones, collectstatic)
├── requirements.txt        # Dependencias Python
├── manage.py               # CLI de Django
│
├── config/                 # Configuración del proyecto Django
│   ├── settings.py         # Settings principal
│   ├── urls.py            # URLs raíz
│   └── wsgi.py/asgi.py    # WSGI/ASGI
│
├── core/                   # App principal
│   ├── models/            # Modelos de BD
│   ├── views/             # Vistas
│   ├── services/          # Lógica de negocio
│   ├── static/            # Archivos estáticos (CSS, JS)
│   └── templates/         # Templates HTML
│
├── templates/              # Templates globales
│   ├── base.html          # Template base
│   └── registration/      # Templates de autenticación
│
└── nginx/                  # Configuración nginx
    ├── Dockerfile          # Imagen nginx personalizada
    ├── templates/          # Configs de nginx
    ├── ssl/               # Certificados SSL (auto-generados)
    └── generate-ssl.sh    # Script para generar certificados
```

---

## 📞 Soporte

Para ayuda adicional:

1. **Logs:** `docker compose logs -f`
2. **Variables:** `cat .env`
3. **Estado:** `docker compose ps`
4. **Documentación Django:** https://docs.djangoproject.com
5. **Documentación nginx:** https://nginx.org/en/docs/

---

## ⚡ Resumen de Comandos Rápidos

```bash
# Desarrollo diario
docker compose up -d                    # Iniciar
docker compose logs -f                  # Ver logs
docker compose restart web              # Reiniciar Django
docker compose exec web python manage.py ... # Comandos Django
docker compose down                     # Detener

# Archivos estáticos
docker compose exec web python manage.py collectstatic --noinput

# Base de datos
docker compose exec web python manage.py migrate
docker compose exec db psql -U postgres -d unidades_moviles

# Producción
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

**¡Listo para desarrollar! 🎉**

Tu entorno replica producción con nginx sirviendo estáticos, HTTPS habilitado y proxy WHEP configurado.
