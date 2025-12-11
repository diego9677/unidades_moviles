from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=250, verbose_name="Nombre")
    port_list = models.TextField(
        verbose_name="Lista de Puertos",
        help_text="Ingrese números de puerto separados por comas (ej: 1001, 1002).",
        # Simple validation for comma separated numbers allowed spaces
        # Validators will be enforced in ModelForms automatically
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        verbose_name="Usuario",
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
