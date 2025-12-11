import requests
import logging
from typing import Dict, List, Any

# Configurar logging
logger = logging.getLogger(__name__)


class APIException(Exception):
    """Excepción personalizada para errores de la API"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class ClientAPIService:
    """
    Servicio para realizar peticiones a la API de clientes
    """

    def __init__(self, api_key: str = None):
        self.base_url = "https://srv4.elittehosting.com"
        self.api_prefix = "/api/clients"
        self.api_key = "0ea740c63299b9a39a647e21b91e34b1722c7b1a9403ec00432ab4e8aeb463c0"

        if not self.api_key:
            raise ValueError("API Key es requerida. Proporciona una API key o configura CLIENT_API_KEY en settings.")

    def _get_headers(self) -> Dict[str, str]:
        """Retorna los headers necesarios para las peticiones"""
        return {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'UnitMobileClient/1.0'
        }

    def _make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> Dict[str, Any]:
        """
        Método base para realizar peticiones HTTP

        Args:
            method: Método HTTP (GET, POST, PUT, DELETE, etc.)
            endpoint: Endpoint de la API (relativo al prefijo)
            data: Datos para el body de la petición
            params: Parámetros de query string

        Returns:
            dict: Respuesta de la API

        Raises:
            APIException: En caso de errores en la petición
        """
        # Construir URL completa concatenando base + prefix + endpoint
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        headers = self._get_headers()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30
            )

            # Log de la petición
            logger.info(f"{method} {url} - Status: {response.status_code}")

            # Verificar si la respuesta fue exitosa
            response.raise_for_status()

            # Intentar parsear como JSON
            try:
                return response.json()
            except ValueError:
                # Si no es JSON válido, retornar texto
                return {"message": response.text, "status_code": response.status_code}

        except requests.exceptions.Timeout:
            error_msg = f"Timeout en petición a {url}"
            logger.error(error_msg)
            raise APIException(error_msg, status_code=408)

        except requests.exceptions.ConnectionError:
            error_msg = f"Error de conexión a {url}"
            logger.error(error_msg)
            raise APIException(error_msg, status_code=503)

        except requests.exceptions.HTTPError as e:
            error_msg = f"Error HTTP {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            try:
                error_data = e.response.json()
            except ValueError:
                error_data = {"detail": e.response.text}
            raise APIException(error_msg, status_code=e.response.status_code, response_data=error_data)

        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg)
            raise APIException(error_msg)

    # ============================
    # ENDPOINTS DE HEALTH CHECK
    # ============================

    def health_check(self) -> Dict[str, Any]:
        """
        Verificar que la API esté funcionando

        Returns:
            dict: Estado de la API
        """
        # Se asume que el health check está en la raíz del prefijo o en /health?
        # Si api_prefix es /api/clients, "/" -> /api/clients/
        return self._make_request("GET", "/")

    # ============================
    # GESTIÓN DE CLIENTES
    # ============================

    def create_client(self, client_name: str, ports: List[int]) -> Dict[str, Any]:
        """
        Crear un nuevo cliente con los puertos especificados

        Args:
            client_name: Nombre del cliente
            ports: Lista de puertos SRT

        Returns:
            dict: Respuesta de la API
        """
        data = {
            "client": client_name,
            "ports": ports
        }
        # Endpoint relativo: /create -> /api/clients/create
        return self._make_request("POST", "/create", data=data)

    def delete_client(self, client_name: str) -> Dict[str, Any]:
        """
        Eliminar un cliente existente

        Args:
            client_name: Nombre del cliente

        Returns:
            dict: Respuesta de la API
        """
        # Endpoint relativo: /nombre -> /api/clients/nombre
        endpoint = f"/{client_name}"
        return self._make_request("DELETE", endpoint)

    def extend_client(self, client_name: str, ports: List[int]) -> Dict[str, Any]:
        """
        Extender un cliente agregando nuevos puertos

        Args:
            client_name: Nombre del cliente
            ports: Lista de nuevos puertos

        Returns:
            dict: Respuesta de la API
        """
        data = {"ports": ports}
        endpoint = f"/{client_name}/extend"
        return self._make_request("POST", endpoint, data=data)

    # ============================
    # CONTROL DE CLIENTES
    # ============================

    def restart_client(self, client_name: str) -> Dict[str, Any]:
        """
        Reiniciar un cliente específico

        Args:
            client_name: Nombre del cliente

        Returns:
            dict: Respuesta de la API
        """
        endpoint = f"/{client_name}/restart"
        return self._make_request("POST", endpoint)

    def stop_client(self, client_name: str) -> Dict[str, Any]:
        """
        Detener un cliente específico

        Args:
            client_name: Nombre del cliente

        Returns:
            dict: Respuesta de la API
        """
        endpoint = f"/{client_name}/stop"
        return self._make_request("POST", endpoint)

    def start_client(self, client_name: str) -> Dict[str, Any]:
        """
        Iniciar un cliente específico

        Args:
            client_name: Nombre del cliente

        Returns:
            dict: Respuesta de la API
        """
        endpoint = f"/{client_name}/start"
        return self._make_request("POST", endpoint)

    def restart_port(self, client_name: str, port: int) -> Dict[str, Any]:
        """
        Reiniciar un puerto específico de un cliente

        Args:
            client_name: Nombre del cliente
            port: Puerto a reiniciar

        Returns:
            dict: Respuesta de la API
        """
        # Endpoint según captura: /clients/nombre/restart-port/puerto
        endpoint = f"/{client_name}/restart-port/{port}"
        return self._make_request("POST", endpoint)


# ============================
# FUNCIONES DE CONVENIENCIA
# ============================

# Instancia global del servicio (se inicializa cuando se proporciona la API key)
_api_service = None


def get_api_service(api_key: str = None) -> ClientAPIService:
    """
    Obtener una instancia del servicio de API

    Args:
        api_key: API key (opcional si ya está configurada)

    Returns:
        ClientAPIService: Instancia del servicio
    """
    global _api_service
    if _api_service is None or api_key:
        _api_service = ClientAPIService(api_key)
    return _api_service

# Funciones de conveniencia que usan la instancia global


def api_health_check(api_key: str = None) -> Dict[str, Any]:
    """Verificar estado de la API"""
    service = get_api_service(api_key)
    return service.health_check()


def api_create_client(client_name: str, ports: List[int], api_key: str = None) -> Dict[str, Any]:
    """Crear cliente"""
    service = get_api_service(api_key)
    return service.create_client(client_name, ports)


def api_delete_client(client_name: str, api_key: str = None) -> Dict[str, Any]:
    """Eliminar cliente"""
    service = get_api_service(api_key)
    return service.delete_client(client_name)


def api_extend_client(client_name: str, ports: List[int], api_key: str = None) -> Dict[str, Any]:
    """Extender cliente con nuevos puertos"""
    service = get_api_service(api_key)
    return service.extend_client(client_name, ports)


def api_restart_client(client_name: str, api_key: str = None) -> Dict[str, Any]:
    """Reiniciar cliente"""
    service = get_api_service(api_key)
    return service.restart_client(client_name)


def api_stop_client(client_name: str, api_key: str = None) -> Dict[str, Any]:
    """Detener cliente"""
    service = get_api_service(api_key)
    return service.stop_client(client_name)


def api_start_client(client_name: str, api_key: str = None) -> Dict[str, Any]:
    """Iniciar cliente"""
    service = get_api_service(api_key)
    return service.start_client(client_name)


def api_restart_port(client_name: str, port: int, api_key: str = None) -> Dict[str, Any]:
    """Reiniciar puerto específico"""
    service = get_api_service(api_key)
    return service.restart_port(client_name, port)
