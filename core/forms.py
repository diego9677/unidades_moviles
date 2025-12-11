from django import forms
from django.contrib.auth.models import User
from .models import Client

class ClientCreateForm(forms.ModelForm):
    username = forms.CharField(label="Usuario", max_length=150, help_text="Nombre de usuario para el panel")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput, help_text="Contraseña para el panel")
    port_list = forms.CharField(label="Lista de Puertos", help_text="Ingrese los puertos separados por coma (ej: 1001, 1002)")

    class Meta:
        model = Client
        fields = ['name', 'port_list']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_port_list(self):
        ports_str = self.cleaned_data.get('port_list')
        try:
            # Validar que sea una lista de enteros separados por coma
            ports = [int(p.strip()) for p in ports_str.split(',') if p.strip()]
            if not ports:
                raise forms.ValidationError("Debe ingresar al menos un puerto.")
        except ValueError:
            raise forms.ValidationError("La lista de puertos debe contener solo números separados por coma.")
        return ports_str

class ClientUpdateForm(forms.ModelForm):
    port_list = forms.CharField(label="Lista de Puertos", help_text="Ingrese los puertos separados por coma (ej: 1001, 1002)")

    class Meta:
        model = Client
        fields = ['name', 'port_list']

    def clean_port_list(self):
        ports_str = self.cleaned_data.get('port_list')
        try:
            ports = [int(p.strip()) for p in ports_str.split(',') if p.strip()]
            if not ports:
                raise forms.ValidationError("Debe ingresar al menos un puerto.")
        except ValueError:
            raise forms.ValidationError("La lista de puertos debe contener solo números separados por coma.")
        return ports_str
