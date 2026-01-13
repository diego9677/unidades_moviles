
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    ROLE_CHOICES = (
        ('client', 'Cliente'),
        ('admin', 'Administrador'),
        # ('parts', 'Piezas'),
        # ('reception', 'Recepción'),
    )

    # email = models.EmailField(max_length=250, unique=True, verbose_name='Email')

    role = models.CharField(max_length=50, choices=ROLE_CHOICES, null=True, blank=True, verbose_name='Rol')

    server = models.ForeignKey(
        "core.Server",
        on_delete=models.SET_NULL,  # Or CASCADE/PROTECT depending on reqs, SET_NULL safer for now
        null=True,
        blank=True,
        related_name="clients",
        verbose_name="Servidor Asignado"
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self) -> str:
        return self.username

    @property
    def is_client(self):
        return self.role == 'client'

    @property
    def is_admin(self):
        return self.role == 'admin'
