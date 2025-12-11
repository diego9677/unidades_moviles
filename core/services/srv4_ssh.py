import paramiko
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SSHException(Exception):
    """Excepción para errores de SSH"""
    pass

class ClientSSHService:
    """
    Servicio para gestionar clientes mediante comandos SSH directos.
    Comando base: /usr/local/bin/manage_client
    """

    def __init__(self):
        # Credenciales hardcodeadas (Entorno de pruebas)
        self.host = 'srv4.elittehosting.com'
        self.port = 22
        self.user = 'root'
        self.password = '312869Sc*/'
        self.key_path = None
        self.command_path = "/usr/local/bin/manage_client"

    def _get_connection(self):
        """Establece y retorna una conexión SSH"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.host,
                'port': self.port,
                'username': self.user,
                'timeout': 10
            }

            if self.key_path:
                connect_kwargs['key_filename'] = self.key_path
            elif self.password:
                connect_kwargs['password'] = self.password
            else:
                raise SSHException("No se han configurado credenciales SSH (Password o Key)")

            client.connect(**connect_kwargs)
            return client
        except Exception as e:
            logger.error(f"Error conectando por SSH: {str(e)}")
            raise SSHException(f"Error de conexión SSH: {str(e)}")

    def _run_command(self, args: List[str]) -> Dict[str, Any]:
        """
        Ejecuta el comando manage_client con los argumentos dados.
        Retorna un diccionario similar al de la API para mantener consistencia.
        """
        import shlex
        # Escapar argumentos para evitar problemas con espacios o caracteres especiales
        safe_args = [shlex.quote(str(arg)) for arg in args]
        full_command = f"{self.command_path} {' '.join(safe_args)}"
        logger.info(f"Ejecutando SSH: {full_command}")

        client = None
        try:
            client = self._get_connection()
            stdin, stdout, stderr = client.exec_command(full_command)
            
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if exit_status != 0:
                logger.error(f"Error SSH ({exit_status}): {error}")
                print(f"DEBUG SSH ERROR: Command '{full_command}' failed with status {exit_status}")
                print(f"STDERR: {error}")
                print(f"STDOUT: {output}")
                raise SSHException(f"Error ejecutando comando: {error or output}")

            # Log para debug (temporal)
            print(f"DEBUG SSH SUCCESS: Command '{full_command}' returned status 0")
            print(f"Remote Output: {output}")
            
            logger.info(f"Resultado SSH: {output}")
            return {
                "status": "success", 
                "message": output,
                "data": {"output": output}
            }

        except SSHException:
            raise
        except Exception as e:
            logger.exception("Error inesperado en ejecución SSH")
            raise SSHException(f"Error inesperado: {str(e)}")
        finally:
            if client:
                client.close()

    # ============================
    # IMPLEMENTACIÓN DE MÉTODOS
    # ============================

    def create_client(self, client_name: str, ports: List[int]) -> Dict[str, Any]:
        """
        CREAR CLIENTE
        Comando: manage_client create <name> <p1> <p2> ...
        """
        args = ["create", client_name] + ports
        return self._run_command(args)

    def delete_client(self, client_name: str) -> Dict[str, Any]:
        """
        ELIMINAR
        Comando: manage_client delete <name>
        """
        return self._run_command(["delete", client_name])

    def start_client(self, client_name: str) -> Dict[str, Any]:
        """
        INICIAR CLIENTE
        Comando: manage_client start <name>
        """
        return self._run_command(["start", client_name])

    def stop_client(self, client_name: str) -> Dict[str, Any]:
        """
        DETENER CLIENTE
        Comando: manage_client stop <name>
        """
        return self._run_command(["stop", client_name])

    def restart_client(self, client_name: str) -> Dict[str, Any]:
        """
        REINICIAR CLIENTE
        Comando: manage_client restart <name>
        """
        return self._run_command(["restart", client_name])

    def restart_port(self, client_name: str, port: int) -> Dict[str, Any]:
        """
        REINICIAR PUERTO ESPECIFICO
        Comando: manage_client restart-port <name> <port>
        """
        return self._run_command(["restart-port", client_name, port])

    def extend_client(self, client_name: str, ports: List[int]) -> Dict[str, Any]:
        """
        AGREGAR PUERTOS A FUTURO
        Comando: manage_client extend <name> <p1> <p2> ...
        """
        args = ["extend", client_name] + ports
        return self._run_command(args)

# Instancia global para uso fácil
def get_ssh_service() -> ClientSSHService:
    return ClientSSHService()
