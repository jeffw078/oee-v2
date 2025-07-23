from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Por enquanto, apenas uma URL básica
    path('admin/', views.painel_admin, name='painel_admin'),
]