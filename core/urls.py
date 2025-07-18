from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('admin/', views.painel_admin, name='painel_admin'),
    path('admin/soldadores/', views.gerenciar_soldadores, name='gerenciar_soldadores'),
    path('admin/componentes/', views.gerenciar_componentes, name='gerenciar_componentes'),
    path('admin/tipos-parada/', views.gerenciar_tipos_parada, name='gerenciar_tipos_parada'),
    path('admin/apontamentos/', views.editar_apontamentos, name='editar_apontamentos'),
    path('admin/atualizar-apontamento/', views.atualizar_apontamento, name='atualizar_apontamento'),
    path('admin/logs/', views.logs_auditoria, name='logs_auditoria'),
    #path('api/sync/status_conexao/', views.status_conexao, name='status_conexao'),
    #path('api/sync/sincronizar_dados/', views.sincronizar_dados, name='sincronizar_dados'),
]