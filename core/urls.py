from django.urls import path
from .views import (
    HomeView,
    ClientListView,
    ClientCreateView,
    ClientUpdateView,
    ClientDeleteView,
    ClientActionView,
    PortRestartView,
    ServerListView,
    ServerCreateView,
    ServerUpdateView,
    ServerDeleteView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/add/', ClientCreateView.as_view(), name='client_add'),
    path('clients/<int:pk>/edit/', ClientUpdateView.as_view(), name='client_edit'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
    path('clients/<str:client_name>/action/<str:action>/', ClientActionView.as_view(), name='client_action'),
    path('clients/<str:client_name>/ports/<int:port>/restart/', PortRestartView.as_view(), name='port_restart'),
    
    # Server URLs
    path('servers/', ServerListView.as_view(), name='server_list'),
    path('servers/add/', ServerCreateView.as_view(), name='server_add'),
    path('servers/<int:pk>/edit/', ServerUpdateView.as_view(), name='server_edit'),
    path('servers/<int:pk>/delete/', ServerDeleteView.as_view(), name='server_delete'),
]
