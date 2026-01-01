from django import forms
from .models import Server, User


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ['host', 'api_key', 'initial_port', 'final_port']
        widgets = {
            'api_key': forms.PasswordInput(render_value=True),
        }


class ClientCreateForm(forms.ModelForm):
    username = forms.CharField(label="Usuario", max_length=150, help_text="Nombre de usuario para el panel")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput, help_text="Contraseña para el panel")
    num_ports = forms.IntegerField(min_value=1, initial=1, label="Cantidad de Puertos", help_text="Número de puertos a asignar automáticamente")

    class Meta:
        model = User
        fields = ['server']
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
    class Meta:
        model = User
        fields = ['server']


