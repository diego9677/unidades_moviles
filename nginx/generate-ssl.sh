#!/bin/sh

# Script para generar certificados SSL autofirmados si no existen

SSL_DIR="/etc/nginx/ssl"
CERT_FILE="$SSL_DIR/localhost.crt"
KEY_FILE="$SSL_DIR/localhost.key"

# Crear directorio si no existe
mkdir -p $SSL_DIR

# Generar certificados solo si no existen
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "Generando certificados SSL autofirmados para localhost..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $KEY_FILE \
        -out $CERT_FILE \
        -subj "/C=MX/ST=State/L=City/O=Organization/OU=Department/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1"
    echo "Certificados SSL generados exitosamente."
else
    echo "Los certificados SSL ya existen, omitiendo generación."
fi
