from django.urls import path
from . import views

app_name = 'qualidade'

urlpatterns = [
    # URLs de qualidade
    path('', views.painel_qualidade, name='painel_qualidade'),
    path('defeitos/', views.lista_defeitos, name='lista_defeitos'),
    path('adicionar_defeito/', views.adicionar_defeito, name='adicionar_defeito'),
    path('inspecoes/', views.lista_inspecoes, name='lista_inspecoes'),
]