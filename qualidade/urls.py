# qualidade/urls.py - VERSÃO COMPLETA

from django.urls import path
from . import views

app_name = 'qualidade'

urlpatterns = [
    # Painel principal
    path('painel/', views.painel_qualidade, name='painel_qualidade'),
    
    # APIs de defeitos
    path('registrar_defeito/', views.registrar_defeito, name='registrar_defeito'),
    path('buscar_apontamentos/', views.buscar_apontamentos_soldador, name='buscar_apontamentos'),
    path('calcular_qualidade/', views.calcular_qualidade_tempo_real, name='calcular_qualidade'),
]