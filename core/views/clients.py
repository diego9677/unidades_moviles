from django.views.generic import CreateView, UpdateView, DeleteView, ListView, View
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
import logging

from core.models import Client
from core.forms import ClientCreateForm, ClientUpdateForm
from core.services import client_ssh_service

logger = logging.getLogger(__name__)


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'core/client_list.html'
    context_object_name = 'clients'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Procesar la lista de puertos para cada cliente
        for client in context['clients']:
            if client.port_list:
                try:
                    # Convertir "1001, 1002" -> [1001, 1002]
                    client.ports_parsed = [int(p.strip()) for p in client.port_list.split(',') if p.strip()]
                except ValueError:
                    client.ports_parsed = []
            else:
                client.ports_parsed = []
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientCreateForm
    template_name = 'core/client_form.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # 1. Crear usuario de Django
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = User.objects.create_user(username=username, password=password)

                # 2. Preparar datos para el cliente
                self.object = form.save(commit=False)
                self.object.user = user

                # 3. Guardar el cliente primero (necesario para asignar relaciones)
                self.object.save()

                # 4. Obtener puertos disponibles (AUTO-ASSIGN)
                num_ports = form.cleaned_data['num_ports']
                server = self.object.server

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

                    # UPDATE CLIENT MODEL (como string csv, legacy support)
                    self.object.port_list = ", ".join(map(str, ports))
                    self.object.save()

                    # EXECUTE SSH
                    ssh_service = client_ssh_service.get_ssh_service(server)
                    response = ssh_service.create_client(self.object.name, ports)
                    logger.info(f"SSH Response for create client: {response}")
                else:
                    logger.warning(f"Cliente {self.object.name} creado sin servidor asignado. No se generaron puertos ni SSH.")
                    self.object.save()

                messages.success(self.request, f"Cliente {self.object.name} creado exitosamente con puertos: {self.object.port_list}")
                return super().form_valid(form)

        except ValueError as ve:
            messages.error(self.request, f"Error de validación: {str(ve)}")
            return self.form_invalid(form)

        except client_ssh_service.SSHException as e:
            messages.error(self.request, f"Error al crear cliente via SSH: {str(e)}")
            return self.form_invalid(form)
        except Exception as e:
            logger.exception("Error creating client")
            messages.error(self.request, f"Error interno: {str(e)}")
            return self.form_invalid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientUpdateForm
    template_name = 'core/client_form.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        messages.success(self.request, "Cliente actualizado localmente.")
        return super().form_valid(form)


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'core/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        client_name = self.object.name
        user_id = self.object.user_id  # Guardamos el ID para asegurar borrado
        success_url = self.get_success_url()

        try:
            # 1. Llamar a SSH para eliminar
            if self.object.server:
                # Liberar puertos en DB antes (o despues, pero dentro de try)
                self.object.assigned_ports.update(is_available=True, assigned_client=None)

                ssh_service = client_ssh_service.get_ssh_service(self.object.server)
                ssh_service.delete_client(client_name)
            else:
                logger.warning("Eliminando cliente sin servidor asignado, omitiendo SSH.")

            # 2. Eliminar de BD local
            try:
                with transaction.atomic():
                    # Borramos el usuario directamente por ID.
                    if user_id:
                        deleted_count, _ = User.objects.filter(pk=user_id).delete()
                        logger.info(f"Usuario asociado {user_id} eliminado. Registros afectados: {deleted_count}")

                    if Client.objects.filter(pk=self.object.pk).exists():
                        self.object.delete()
                        logger.info(f"Cliente local {client_name} eliminado explícitamente.")

                messages.success(self.request, f"Cliente {client_name} y su usuario eliminados correctamente.")
                return HttpResponseRedirect(success_url)

            except Exception as local_e:
                logger.exception("Error eliminando localmente")
                messages.error(self.request, f"Error eliminando localmente: {str(local_e)}")
                return HttpResponseRedirect(success_url)

        except client_ssh_service.SSHException as e:
            messages.warning(self.request, f"Advertencia: El cliente fue eliminado localmente, pero hubo un error en el servidor remoto: {str(e)}")
            logger.error(f"Error SSH al eliminar {client_name}: {str(e)}")

            try:
                with transaction.atomic():
                    if user_id:
                        User.objects.filter(pk=user_id).delete()
                    if Client.objects.filter(pk=self.object.pk).exists():
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
            client = Client.objects.get(name=client_name)
            if client.server:
                ssh_service = client_ssh_service.get_ssh_service(client.server)

                if action == 'start':
                    ssh_service.start_client(client_name)
                    messages.success(request, f"Cliente {client_name} iniciado.")
                elif action == 'stop':
                    ssh_service.stop_client(client_name)
                    messages.success(request, f"Cliente {client_name} detenido.")
                elif action == 'restart':
                    ssh_service.restart_client(client_name)
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
            client = Client.objects.get(name=client_name)
            if client.server:
                ssh_service = client_ssh_service.get_ssh_service(client.server)
                ssh_service.restart_port(client_name, port)
                messages.success(request, f"Puerto {port} de {client_name} reiniciado.")
            else:
                messages.warning(request, "El cliente no tiene servidor asignado.")
        except Exception as e:
            logger.exception(f"Error restarting port {port} for {client_name}")
            messages.error(request, f"Error al reiniciar puerto: {str(e)}")

        return redirect('client_list')
