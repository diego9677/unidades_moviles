from django.contrib import admin
from django.contrib.auth.models import Group
from .models import User


# @admin.register(Client)
# class ClientAdmin(admin.ModelAdmin):
#     list_display = ('name', 'user', 'port_list')
#     search_fields = ('name', 'user__username', 'port_list')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')
    ordering = ('username',)


# Desregistrar el modelo Group si no se utiliza
admin.site.unregister(Group)
