from django.contrib import admin

from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'port_list')
    search_fields = ('name', 'user__username', 'port_list')
