import requests
import logging
from typing import List, Dict, Any

from core.models import Server

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Excepción para errores de API"""
    pass


class ClientAPIService:
    """
    Servicio para gestionar clientes mediante API REST.
    """

    def __init__(self, server: Server):
        self.server = server
        self.base_url = f"https://{server.host}/api"
        self.api_key = getattr(server, 'api_key', 'super_secret_key')
        self.timeout = 30

    def _make_request(self, method: str, endpoint: str, data: dict = None) -> Dict[str, Any]:
        """
        Realiza una petición HTTP a la API.
        Retorna un diccionario similar al SSH para mantener consistencia.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'TuApp/1.0',
        }

        print(url)
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 401:
                raise APIException("API Key inválida")

            if not response.ok:
                error_detail = "Error desconocido"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', error_detail)
                except Exception as e:
                    print(e)
                    error_detail = response.text or f"HTTP {response.status_code}"

                raise APIException(f"Error en API: {error_detail}")

            api_response = response.json()

            # Convertir respuesta de API al formato esperado
            return {
                "status": "success" if api_response.get('success', True) else "error",
                "message": api_response.get('message', 'Operación completada'),
                "data": api_response
            }

        except requests.exceptions.ConnectionError as e:
            raise APIException(f"No se pudo conectar a la API: {e}")
        except requests.exceptions.Timeout:
            raise APIException("Timeout conectando a la API")
        except APIException as e:
            print(e)
            raise
        except Exception as e:
            raise APIException(f"Error inesperado: {str(e)}")

    # ============================
    # IMPLEMENTACIÓN DE MÉTODOS
    # ============================

    def create_client(self, client_name: str, ports: List[int]) -> Dict[str, Any]:
        """
        CREAR CLIENTE
        POST /clients/create
        """
        data = {
            'client': client_name,
            'ports': ports
        }
        return self._make_request('POST', '/clients/create', data)

    def delete_client(self, client_name: str) -> Dict[str, Any]:
        """
        ELIMINAR CLIENTE
        DELETE /clients/{client_name}
        """
        return self._make_request('DELETE', f'/clients/{client_name}')

    def start_client(self, client_name: str) -> Dict[str, Any]:
        """
        INICIAR CLIENTE
        POST /clients/{client_name}/start
        """
        return self._make_request('POST', f'/clients/{client_name}/start')

    def stop_client(self, client_name: str) -> Dict[str, Any]:
        """
        DETENER CLIENTE
        POST /clients/{client_name}/stop
        """
        return self._make_request('POST', f'/clients/{client_name}/stop')

    def restart_client(self, client_name: str) -> Dict[str, Any]:
        """
        REINICIAR CLIENTE
        POST /clients/{client_name}/restart
        """
        return self._make_request('POST', f'/clients/{client_name}/restart')

    def restart_port(self, client_name: str, port: int) -> Dict[str, Any]:
        """
        REINICIAR PUERTO ESPECIFICO
        POST /clients/{client_name}/ports/{port}/restart
        """
        return self._make_request('POST', f'/clients/{client_name}/ports/{port}/restart')

    def extend_client(self, client_name: str, ports: List[int]) -> Dict[str, Any]:
        """
        AGREGAR PUERTOS
        POST /clients/{client_name}/extend
        """
        data = {'ports': ports}
        return self._make_request('POST', f'/clients/{client_name}/extend', data)


def get_api_service(server) -> ClientAPIService:
    """Factory function para crear el servicio API"""
    return ClientAPIService(server)
