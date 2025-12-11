from django.urls import path
from .views import (
    HomeView,
    ClientListView,
    ClientCreateView,
    ClientUpdateView,
    ClientDeleteView,
    ClientActionView,
    PortRestartView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/add/', ClientCreateView.as_view(), name='client_add'),
    path('clients/<int:pk>/edit/', ClientUpdateView.as_view(), name='client_edit'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
    path('clients/<str:client_name>/action/<str:action>/', ClientActionView.as_view(), name='client_action'),
    path('clients/<str:client_name>/ports/<int:port>/restart/', PortRestartView.as_view(), name='port_restart'),
]
