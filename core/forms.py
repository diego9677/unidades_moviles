from django import forms
from django.contrib.auth.models import User
from .models import Client, Server

class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = '__all__'
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }

class ClientCreateForm(forms.ModelForm):
    username = forms.CharField(label="Usuario", max_length=150, help_text="Nombre de usuario para el panel")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput, help_text="Contraseña para el panel")
    num_ports = forms.IntegerField(min_value=1, initial=1, label="Cantidad de Puertos", help_text="Número de puertos a asignar automáticamente")
    
    class Meta:
        model = Client
        fields = ['server', 'name'] # port_list removed from fields, logic handles it
        help_texts = {
             'server': 'Seleccione el servidor donde se alojará este cliente.',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        server = cleaned_data.get('server')
        num_ports = cleaned_data.get('num_ports')
        
        if server and num_ports:
            # Check if server has enough available ports
            available_count = server.ports.filter(is_available=True).count()
            if available_count < num_ports:
                raise forms.ValidationError(f"El servidor seleccionado solo tiene {available_count} puertos disponibles (se solicitaron {num_ports}).")
        
        return cleaned_data

class ClientUpdateForm(forms.ModelForm):
    port_list = forms.CharField(label="Lista de Puertos", help_text="Ingrese los puertos separados por coma (ej: 1001, 1002)")

    class Meta:
        model = Client
        fields = ['server', 'name', 'port_list']

    def clean(self):
        cleaned_data = super().clean()
        server = cleaned_data.get('server')
        ports_str = cleaned_data.get('port_list')
        
        # If server or ports didn't change, we might skip re-validation if logic gets complex, 
        # but safely re-validating is better to avoid race conditions or manual DB changes.
        # Ideally exclude *current* client's usage from check, but Server.get_used_ports() includes us.
        # We need to handle "self collision" if we are editing.
        
        if not ports_str:
             return cleaned_data
             
        try:
            ports = [int(p.strip()) for p in ports_str.split(',') if p.strip()]
        except ValueError:
            self.add_error('port_list', "Invalid format")
            return cleaned_data
            
        if server and self.instance.pk:
            # We must exclude our own ports from the "used" check if we are keeping them.
            # However check_ports_availability checks against get_used_ports which queries DB.
            # Since we haven't saved, DB has old ports.
            # We can implement a more robust check or just proceed. 
            # Simple fix: get used ports, remove *our* stored ports, then check.
            
            # This logic fits better in model or service, but for now here:
            used_ports = server.get_used_ports()
            
            # Remove current instance ports from used_ports
            current_ports_str = self.instance.port_list
            if current_ports_str:
                 try:
                    current_ports = [int(p.strip()) for p in current_ports_str.split(',') if p.strip()]
                    for p in current_ports:
                        if p in used_ports:
                            used_ports.remove(p)
                 except: 
                     pass
            
            # Now check
            for port in ports:
                 if not (server.initial_port <= port <= server.final_port):
                     raise forms.ValidationError(f"El puerto {port} está fuera del rango ({server.initial_port}-{server.final_port})")
                 if port in used_ports:
                     raise forms.ValidationError(f"El puerto {port} ya está en uso.")
                     
        elif server:
             # New server assignment (or new object, handled by CreateForm, but UpdateForm can also set server)
             is_valid, error_msg = server.check_ports_availability(ports)
             if not is_valid:
                 raise forms.ValidationError(error_msg)
        
        return cleaned_data
