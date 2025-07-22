from django.urls import path
from . import views

app_name = 'soldagem'

urlpatterns = [
    # URLs principais
    path('', views.selecao_soldador, name='selecao_soldador'),
    path('login_soldador/', views.login_soldador, name='login_soldador'),
    path('apontamento/', views.apontamento, name='apontamento'),
    path('finalizar_turno/', views.finalizar_turno, name='finalizar_turno'),
    
    # APIs de apontamento
    path('api/iniciar_modulo/', views.iniciar_modulo, name='iniciar_modulo'),
    path('api/iniciar_componente/', views.iniciar_componente, name='iniciar_componente'),
    path('api/finalizar_componente/', views.finalizar_componente, name='finalizar_componente'),
    
    # APIs de paradas
    path('api/iniciar_parada/', views.iniciar_parada, name='iniciar_parada'),
    path('api/finalizar_parada/', views.finalizar_parada, name='finalizar_parada'),
    path('api/buscar_tipos_parada/', views.buscar_tipos_parada, name='buscar_tipos_parada'),
    
    # Painéis específicos
    path('painel_qualidade/', views.painel_qualidade, name='painel_qualidade'),
    path('painel_paradas/', views.painel_paradas, name='painel_paradas'),
    path('painel_manutencao/', views.painel_manutencao, name='painel_manutencao'),
]
