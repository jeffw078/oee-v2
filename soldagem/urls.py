# arquivo: soldagem/urls.py (ATUALIZAR)

from django.urls import path
from . import views

app_name = 'soldagem'

urlpatterns = [
    # URLs principais - FLUXO CORRETO
    path('', views.selecao_soldador, name='selecao_soldador'),
    path('login_soldador/', views.login_soldador, name='login_soldador'),
    path('selecao_modulo/', views.selecao_modulo, name='selecao_modulo'),  # NOVA
    path('selecao_componente/', views.selecao_componente, name='selecao_componente'),  # NOVA
    path('processo_soldagem/', views.processo_soldagem, name='processo_soldagem'),  # NOVA
    #path('finalizar_turno/', views.finalizar_turno, name='finalizar_turno'),
    
    # APIs de apontamento
    path('api/iniciar_modulo/', views.iniciar_modulo, name='iniciar_modulo'),
    path('api/iniciar_componente/', views.iniciar_componente, name='iniciar_componente'),
    #path('api/finalizar_componente/', views.finalizar_componente, name='finalizar_componente'),
    
    # APIs de paradas
    #path('api/iniciar_parada/', views.iniciar_parada, name='iniciar_parada'),
    #path('api/finalizar_parada/', views.finalizar_parada, name='finalizar_parada'),
    path('api/buscar_tipos_parada/', views.buscar_tipos_parada, name='buscar_tipos_parada'),
    
    # APIs de status e sincronização
    path('api/status_conexao/', views.status_conexao, name='status_conexao'),  # NOVA
    path('api/sync_offline/', views.sync_offline_data, name='sync_offline'),  # NOVA
    path('api/componentes/', views.listar_componentes, name='listar_componentes'),  # NOVA
    
    # Painéis específicos
    path('painel_qualidade/', views.painel_qualidade, name='painel_qualidade'),
    path('painel_paradas/', views.painel_paradas, name='painel_paradas'),
    path('painel_manutencao/', views.painel_manutencao, name='painel_manutencao'),
]