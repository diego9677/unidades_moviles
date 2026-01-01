from django.db import models


class Server(models.Model):
    host = models.CharField(max_length=255, verbose_name="Host")
    api_key = models.CharField(max_length=255, verbose_name="Clave API", help_text="Clave API para autenticación")
    initial_port = models.IntegerField(verbose_name="Puerto Inicial", help_text="Inicio del rango de puertos")
    final_port = models.IntegerField(verbose_name="Puerto Final", help_text="Fin del rango de puertos")

    class Meta:
        verbose_name = "Servidor"
        verbose_name_plural = "Servidores"

    def __str__(self):
        return f"{self.host} ({self.initial_port}-{self.final_port})"

    @property
    def get_used_ports_count(self):
        return self.ports.filter(is_available=False).count()

    @property
    def get_usage_percent(self):
        total = self.ports.count()
        if total == 0:
            return 0
        return int((self.get_used_ports_count / total) * 100)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Generate ports if new or range changed (simplified: always check/generate missing)
        self.generate_ports()

    def generate_ports(self):
        """Genera registros PortServer para el rango definido"""
        existing_ports = set(self.ports.values_list('port_number', flat=True))
        new_ports = []
        for port in range(self.initial_port, self.final_port + 1):
            if port not in existing_ports:
                new_ports.append(PortServer(server=self, port_number=port))

        if new_ports:
            PortServer.objects.bulk_create(new_ports)

    def check_ports_availability(self, ports_to_check):
        """
        Verifica si los puertos están libres en la tabla PortServer.
        """
        for port in ports_to_check:
            # Check range
            if not (self.initial_port <= port <= self.final_port):
                return False, f"El puerto {port} está fuera del rango permitido ({self.initial_port}-{self.final_port})"

            # Check availability in DB
            port_obj = self.ports.filter(port_number=port).first()
            if not port_obj:
                # Should not happen if generate_ports worked, but safe check
                return False, f"El puerto {port} no está gestionado por este servidor."

            if not port_obj.is_available:
                return False, f"El puerto {port} ya está ocupado."

        return True, None


class PortServer(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='ports')
    port_number = models.IntegerField(verbose_name="Número de Puerto")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    assigned_client = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_ports',
        verbose_name="Cliente Asignado"
    )

    class Meta:
        verbose_name = "Puerto de Servidor"
        verbose_name_plural = "Puertos de Servidores"
        unique_together = ('server', 'port_number')

    def __str__(self):
        status = "Libre" if self.is_available else "Ocupado"
        return f"{self.server.host}:{self.port_number} ({status})"
