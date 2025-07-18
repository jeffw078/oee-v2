from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    path('', views.dashboard_principal, name='dashboard_principal'),
    path('oee/', views.relatorio_oee_detalhado, name='relatorio_oee_detalhado'),
    path('pontos-melhoria/', views.pontos_melhoria, name='pontos_melhoria'),
    path('paradas/', views.relatorio_paradas, name='relatorio_paradas'),
    path('utilizacao-turnos/', views.utilizacao_turnos, name='utilizacao_turnos'),
    
    # APIs para gráficos
    path('api/oee_historico/', views.api_oee_historico, name='api_oee_historico'),
    path('api/eficiencia_dispersao/', views.api_eficiencia_dispersao, name='api_eficiencia_dispersao'),
    path('api/paradas_categoria/', views.api_paradas_categoria, name='api_paradas_categoria'),
]