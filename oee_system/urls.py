from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# Customizar admin
admin.site.site_header = "Sistema OEE - Administração"
admin.site.site_title = "OEE Admin"
admin.site.index_title = "Gerenciamento do Sistema OEE"

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Redirecionar raiz para soldagem
    path('', lambda request: redirect('soldagem:selecao_soldador')),
    
    # Apps do sistema
    path('soldagem/', include('soldagem.urls')),
    path('qualidade/', include('qualidade.urls')),
    path('core/', include('core.urls')),
    
]

# Servir arquivos estáticos e media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)