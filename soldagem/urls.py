from django.urls import path
from . import views

app_name = 'soldagem'

urlpatterns = [
    path('', views.selecao_soldador, name='selecao_soldador'),
    path('login_soldador/', views.login_soldador, name='login_soldador'),
    path('apontamento/', views.apontamento, name='apontamento'),
    path('iniciar_modulo/', views.iniciar_modulo, name='iniciar_modulo'),
    path('iniciar_componente/', views.iniciar_componente, name='iniciar_componente'),
    path('finalizar_componente/', views.finalizar_componente, name='finalizar_componente'),
    path('finalizar_turno/', views.finalizar_turno, name='finalizar_turno'),
]