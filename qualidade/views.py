from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TipoDefeito, Defeito, InspecaoQualidade
from soldagem.models import Soldador, Apontamento

def painel_qualidade(request):
    """Painel principal de qualidade"""
    context = {
        'titulo': 'Painel de Qualidade',
        'total_defeitos': Defeito.objects.count(),
        'total_inspecoes': InspecaoQualidade.objects.count(),
        'defeitos_recentes': Defeito.objects.select_related(
            'tipo_defeito', 'soldador__usuario', 'apontamento__componente'
        ).order_by('-data_deteccao')[:10]
    }
    return render(request, 'qualidade/painel_qualidade.html', context)

def lista_defeitos(request):
    """Lista todos os defeitos"""
    defeitos = Defeito.objects.select_related(
        'tipo_defeito', 'soldador__usuario', 'apontamento__componente'
    ).order_by('-data_deteccao')
    
    context = {
        'titulo': 'Lista de Defeitos',
        'defeitos': defeitos
    }
    return render(request, 'qualidade/lista_defeitos.html', context)

@csrf_exempt
def adicionar_defeito(request):
    """Adiciona um novo defeito"""
    if request.method == 'POST':
        # Implementar lógica para adicionar defeito
        # Por enquanto, placeholder
        messages.success(request, 'Defeito adicionado com sucesso!')
        return redirect('qualidade:lista_defeitos')
    
    tipos_defeito = TipoDefeito.objects.filter(ativo=True)
    soldadores = Soldador.objects.filter(ativo=True)
    
    context = {
        'titulo': 'Adicionar Defeito',
        'tipos_defeito': tipos_defeito,
        'soldadores': soldadores
    }
    return render(request, 'qualidade/adicionar_defeito.html', context)

def lista_inspecoes(request):
    """Lista todas as inspeções"""
    inspecoes = InspecaoQualidade.objects.select_related(
        'soldador__usuario', 'usuario_qualidade'
    ).order_by('-data_inspecao')
    
    context = {
        'titulo': 'Lista de Inspeções',
        'inspecoes': inspecoes
    }
    return render(request, 'qualidade/lista_inspecoes.html', context)