from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('admin-dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('gerenciar-soldadores/', views.gerenciar_soldadores, name='gerenciar_soldadores'),
    path('gerenciar-componentes/', views.gerenciar_componentes, name='gerenciar_componentes'),
    path('gerenciar-paradas/', views.gerenciar_paradas, name='gerenciar_paradas'),
    path('editar-apontamentos/', views.editar_apontamentos, name='editar_apontamentos'),
    path('api/excluir-registro/', views.api_excluir_registro, name='api_excluir_registro'),
]