from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from core.models import Client


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Determinar si el usuario es administrador
        is_admin = user.is_staff
        context['is_admin'] = is_admin

        if is_admin:
            # Lógica para administradores
            clients = Client.objects.select_related('server', 'user').all()
            context['clients'] = clients

            # Obtener cliente seleccionado desde parámetro GET
            selected_client_id = self.request.GET.get('client_id')
            selected_client = None
            ports_info = []

            if selected_client_id:
                try:
                    selected_client = Client.objects.select_related('server').get(pk=selected_client_id)
                    ports_info = self._get_ports_info(selected_client)
                except Client.DoesNotExist:
                    pass

            context['selected_client'] = selected_client
            context['ports_info'] = ports_info

        else:
            # Lógica para clientes
            try:
                client = Client.objects.select_related('server').get(user=user)
                context['client'] = client
                context['ports_info'] = self._get_ports_info(client)
            except Client.DoesNotExist:
                context['client'] = None
                context['ports_info'] = []

        return context

    def _get_ports_info(self, client):
        """
        Obtiene la información de puertos de un cliente para mostrar en las tarjetas.
        Retorna una lista de diccionarios con la información necesaria para la conexión SRT.
        """
        if not client or not client.server:
            return []

        ports_info = []
        # Obtener puertos asignados desde la relación assigned_ports
        assigned_ports = client.assigned_ports.select_related('server').order_by('port_number')

        for port in assigned_ports:
            ports_info.append({
                'port_number': port.port_number,
                'host': port.server.host,
                'client_name': client.name,
                'is_available': port.is_available,
                'server_name': str(port.server),
            })

        return ports_info
