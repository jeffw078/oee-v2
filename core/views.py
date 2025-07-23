from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# CORRIGIR: Importar do soldagem, não do core
from soldagem.models import Usuario

@login_required
def painel_admin(request):
    """Painel administrativo básico"""
    return render(request, 'core/admin.html', {
        'titulo': 'Painel Administrativo',
        'mensagem': 'Funcionalidade em desenvolvimento'
    })