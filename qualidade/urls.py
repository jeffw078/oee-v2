from django.urls import path
from . import views

app_name = 'qualidade'

urlpatterns = [
    path('painel/', views.painel_qualidade, name='painel_qualidade'),
    path('registrar_defeito/', views.registrar_defeito, name='registrar_defeito'),
    path('buscar_apontamentos/', views.buscar_apontamentos_soldador, name='buscar_apontamentos'),
]