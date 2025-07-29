from django.urls import path
from . import views

app_name = 'qualidade'

urlpatterns = [
    path('', views.painel_qualidade, name='painel_qualidade'),
    path('painel/', views.painel_qualidade, name='painel'),
    path('registrar_defeito/', views.registrar_defeito, name='registrar_defeito'),
    path('relatorio/', views.relatorio_qualidade, name='relatorio_qualidade'),
    path('api/apontamentos_dia/', views.api_apontamentos_dia, name='api_apontamentos_dia'),
]