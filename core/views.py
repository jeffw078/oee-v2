from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Views do core (funcionalidades gerais)
# Por enquanto vazio, pode ser expandido futuramente com:
# - Dashboard geral
# - Relatórios consolidados
# - Configurações do sistema
# - Etc.

def dashboard_geral(request):
    """Dashboard geral do sistema"""
    context = {
        'titulo': 'Dashboard Geral'
    }
    return render(request, 'core/dashboard.html', context)