from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib import messages

from core.models import Server
from core.forms import ServerForm

class ServerListView(ListView):
    model = Server
    template_name = 'core/server_list.html'
    context_object_name = 'servers'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class ServerCreateView(CreateView):
    model = Server
    form_class = ServerForm
    template_name = 'core/server_form.html'
    success_url = reverse_lazy('server_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Servidor agregado exitosamente.")
        return super().form_valid(form)

class ServerUpdateView(UpdateView):
    model = Server
    form_class = ServerForm
    template_name = 'core/server_form.html'
    success_url = reverse_lazy('server_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Servidor actualizado.")
        return super().form_valid(form)

class ServerDeleteView(DeleteView):
    model = Server
    template_name = 'core/server_confirm_delete.html'
    success_url = reverse_lazy('server_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Servidor eliminado.")
        return super().delete(request, *args, **kwargs)
