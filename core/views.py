

from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView, View
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
import logging

from .models import Client
from .forms import ClientCreateForm, ClientUpdateForm
# from .services import srv4_moviles # Replaced by SSH
from .services import srv4_ssh

logger = logging.getLogger(__name__)

# Instancia del servicio SSH
ssh_service = srv4_ssh.get_ssh_service()

class ClientListView(ListView):
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


class ClientCreateView(CreateView):
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
                
                # 3. Llamar a la API / SSH
                ports_str = form.cleaned_data['port_list']
                ports = [int(p.strip()) for p in ports_str.split(',') if p.strip()]
                
                # CAMBIO: Usar SSH Service
                response = ssh_service.create_client(self.object.name, ports)
                
                logger.info(f"SSH Response for create client: {response}")
                
                self.object.save()
                
                messages.success(self.request, f"Cliente {self.object.name} creado exitosamente.")
                return super().form_valid(form)

        except srv4_ssh.SSHException as e:
            messages.error(self.request, f"Error al crear cliente via SSH: {str(e)}")
            return self.form_invalid(form)
        except Exception as e:
            logger.exception("Error creating client")
            messages.error(self.request, f"Error interno: {str(e)}")
            return self.form_invalid(form)


class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientUpdateForm
    template_name = 'core/client_form.html'
    success_url = reverse_lazy('client_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Cliente actualizado localmente.")
        return super().form_valid(form)


class ClientDeleteView(DeleteView):
    model = Client
    template_name = 'core/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')

    def form_valid(self, form):
        client_name = self.object.name
        user_id = self.object.user_id  # Guardamos el ID para asegurar borrado
        success_url = self.get_success_url()
        
        try:
            # 1. Llamar a SSH para eliminar
            ssh_service.delete_client(client_name)
            
            # 2. Eliminar de BD local
            try:
                with transaction.atomic():
                     # Borramos el usuario directamente por ID.
                     # Al tener on_delete=CASCADE en el modelo Client, esto debería borrar el cliente también.
                     # Pero por seguridad y claridad explícita:
                    if user_id:
                        # Usamos filter().delete() que es seguro si no existe
                        deleted_count, _ = User.objects.filter(pk=user_id).delete()
                        logger.info(f"Usuario asociado {user_id} eliminado. Registros afectados: {deleted_count}")
                    
                    # Si por alguna razón el cliente sigue vivo (ej: no cascada), lo rematamos
                    if Client.objects.filter(pk=self.object.pk).exists():
                        self.object.delete()
                        logger.info(f"Cliente local {client_name} eliminado explícitamente.")

                messages.success(self.request, f"Cliente {client_name} y su usuario eliminados correctamente.")
                return HttpResponseRedirect(success_url)
                
            except Exception as local_e:
                 logger.exception("Error eliminando localmente")
                 messages.error(self.request, f"Error eliminando localmente: {str(local_e)}")
                 return HttpResponseRedirect(success_url)
                
        except srv4_ssh.SSHException as e:
            # Si falla SSH, notificamos pero procedemos a borrar localmente
            messages.warning(self.request, f"Advertencia: El cliente fue eliminado localmente, pero hubo un error en el servidor remoto: {str(e)}")
            logger.error(f"Error SSH al eliminar {client_name}: {str(e)}")
            
            try:
                with transaction.atomic():
                    if user_id:
                        User.objects.filter(pk=user_id).delete()
                        logger.info(f"Usuario {user_id} eliminado (Fallback SSH).")
                    
                    if Client.objects.filter(pk=self.object.pk).exists():
                        self.object.delete()
                
                return HttpResponseRedirect(success_url)
            except Exception as local_e:
                 messages.error(self.request, f"Error eliminando localmente: {str(local_e)}")
                 return HttpResponseRedirect(success_url)

        except Exception as e:
            messages.error(self.request, f"Error interno al eliminar: {str(e)}")
            return HttpResponseRedirect(success_url)

class ClientActionView(View):
    def post(self, request, client_name, action):
        try:
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
        except Exception as e:
            logger.exception(f"Error executing action {action} on {client_name}")
            messages.error(request, f"Error al ejecutar {action}: {str(e)}")
        
        return redirect('client_list')


class PortRestartView(View):
    def post(self, request, client_name, port):
        try:
            ssh_service.restart_port(client_name, port)
            messages.success(request, f"Puerto {port} de {client_name} reiniciado.")
        except Exception as e:
            logger.exception(f"Error restarting port {port} for {client_name}")
            messages.error(request, f"Error al reiniciar puerto: {str(e)}")
        
        return redirect('client_list')

class HomeView(TemplateView):
    template_name = 'index.html'
