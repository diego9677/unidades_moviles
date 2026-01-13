from django.views.generic import CreateView, UpdateView, DeleteView, ListView, View
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
import logging

from core.models import User
from core.forms import ClientCreateForm, ClientUpdateForm
# from core.services import client_ssh_service
from core.services import client_api_service

logger = logging.getLogger(__name__)


class ClientListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'core/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        return User.objects.filter(role='client').select_related('server').prefetch_related('assigned_ports')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Procesar la lista de puertos para cada cliente desde assigned_ports
        for client in context['clients']:
            client.ports_parsed = list(client.assigned_ports.order_by('port_number').values_list('port_number', flat=True))
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = ClientCreateForm
    template_name = 'core/client_form.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # 1. Crear usuario con rol de cliente
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                server = form.cleaned_data.get('server')

                self.object = User.objects.create_user(
                    username=username,
                    password=password,
                    role='client',
                    server=server
                )

                # 2. Obtener puertos disponibles (AUTO-ASSIGN)
                num_ports = form.cleaned_data['num_ports']

                if server:
                    # LOCK & FETCH PORTS
                    # Select N available ports ensuring concurrency safety
                    available_ports = list(server.ports.filter(is_available=True).select_for_update().order_by('port_number')[:num_ports])

                    if len(available_ports) < num_ports:
                        raise ValueError(f"No hay suficientes puertos disponibles. Solicitados: {num_ports}, Disponibles: {len(available_ports)}")

                    # EXTRACT NUMBERS
                    ports = [p.port_number for p in available_ports]

                    # ASSIGN PORTS IN DB
                    for port_obj in available_ports:
                        port_obj.is_available = False
                        port_obj.assigned_client = self.object
                        port_obj.save()

                    # EXECUTE API
                    api_service = client_api_service.get_api_service(server)
                    response = api_service.create_client(self.object.username, ports)
                    logger.info(f"API Response for create client: {response}")
                    
                    messages.success(self.request, f"Cliente {self.object.username} creado exitosamente con {len(ports)} puertos")
                else:
                    logger.warning(f"Cliente {self.object.username} creado sin servidor asignado. No se generaron puertos.")
                    messages.success(self.request, f"Cliente {self.object.username} creado exitosamente sin servidor")

                return super().form_valid(form)

        except ValueError as ve:
            messages.error(self.request, f"Error de validación: {str(ve)}")
            return self.form_invalid(form)

        except client_api_service.APIException as e:
            messages.error(self.request, f"Error al crear cliente via API: {str(e)}")
            return self.form_invalid(form)
        except Exception as e:
            logger.exception("Error creating client")
            messages.error(self.request, f"Error interno: {str(e)}")
            return self.form_invalid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ClientUpdateForm
    template_name = 'core/client_form.html'
    success_url = reverse_lazy('client_list')

    def get_queryset(self):
        return User.objects.filter(role='client')

    def form_valid(self, form):
        messages.success(self.request, "Cliente actualizado localmente.")
        return super().form_valid(form)


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'core/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')

    def get_queryset(self):
        return User.objects.filter(role='client')

    def form_valid(self, form):
        username = self.object.username
        success_url = self.get_success_url()

        try:
            # 1. Llamar a API para eliminar
            if self.object.server:
                # Liberar puertos en DB
                self.object.assigned_ports.update(is_available=True, assigned_client=None)

                api_service = client_api_service.get_api_service(self.object.server)
                api_service.delete_client(username)
            else:
                logger.warning("Eliminando cliente sin servidor asignado, omitiendo API.")

            # 2. Eliminar de BD local
            try:
                with transaction.atomic():
                    if User.objects.filter(pk=self.object.pk).exists():
                        self.object.delete()
                        logger.info(f"Usuario {username} eliminado exitosamente.")

                messages.success(self.request, f"Cliente {username} eliminado correctamente.")
                return HttpResponseRedirect(success_url)

            except Exception as local_e:
                logger.exception("Error eliminando localmente")
                messages.error(self.request, f"Error eliminando localmente: {str(local_e)}")
                return HttpResponseRedirect(success_url)

        except client_api_service.APIException as e:
            messages.warning(self.request, f"Advertencia: El cliente fue eliminado localmente, pero hubo un error en el servidor remoto: {str(e)}")
            logger.error(f"Error API al eliminar {username}: {str(e)}")

            try:
                with transaction.atomic():
                    if User.objects.filter(pk=self.object.pk).exists():
                        self.object.delete()

                return HttpResponseRedirect(success_url)
            except Exception as local_e:
                messages.error(self.request, f"Error eliminando localmente: {str(local_e)}")
                return HttpResponseRedirect(success_url)

        except Exception as e:
            messages.error(self.request, f"Error interno al eliminar: {str(e)}")
            return HttpResponseRedirect(success_url)


class ClientActionView(LoginRequiredMixin, View):
    def post(self, request, client_name, action):
        try:
            client = User.objects.get(username=client_name, role='client')
            if client.server:
                api_service = client_api_service.get_api_service(client.server)

                if action == 'start':
                    api_service.start_client(client_name)
                    messages.success(request, f"Cliente {client_name} iniciado.")
                elif action == 'stop':
                    api_service.stop_client(client_name)
                    messages.success(request, f"Cliente {client_name} detenido.")
                elif action == 'restart':
                    api_service.restart_client(client_name)
                    messages.success(request, f"Cliente {client_name} reiniciado.")
                else:
                    messages.error(request, f"Acción desconocida: {action}")
            else:
                messages.warning(request, f"El cliente {client_name} no tiene servidor asignado.")
        except Exception as e:
            logger.exception(f"Error executing action {action} on {client_name}")
            messages.error(request, f"Error al ejecutar {action}: {str(e)}")

        return redirect('client_list')


class PortRestartView(LoginRequiredMixin, View):
    def post(self, request, client_name, port):
        try:
            client = User.objects.get(username=client_name, role='client')
            if client.server:
                api_service = client_api_service.get_api_service(client.server)
                api_service.restart_port(client_name, port)
                messages.success(request, f"Puerto {port} de {client_name} reiniciado.")
            else:
                messages.warning(request, "El cliente no tiene servidor asignado.")
        except Exception as e:
            logger.exception(f"Error restarting port {port} for {client_name}")
            messages.error(request, f"Error al reiniciar puerto: {str(e)}")

        return redirect('client_list')

