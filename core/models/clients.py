from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=250, verbose_name="Nombre")
    port_list = models.TextField(verbose_name="Lista de Puertos")

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        verbose_name="Usuario",
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
