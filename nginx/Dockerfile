FROM nginx:stable-alpine

# Instalar openssl para generar certificados SSL
RUN apk add --no-cache openssl

# Copiar script de generación de certificados
COPY generate-ssl.sh /docker-entrypoint.d/40-generate-ssl.sh
RUN chmod +x /docker-entrypoint.d/40-generate-ssl.sh
