from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

# CORRIGIR: Importar do soldagem, não do core
from soldagem.models import Apontamento, Soldador, Usuario
from .models import TipoDefeito, Defeito

def painel_qualidade(request):
    """Painel básico de qualidade"""
    tipos_defeito = TipoDefeito.objects.filter(ativo=True)
    
    # Buscar apontamentos do dia atual
    hoje = timezone.now().date()
    apontamentos_hoje = Apontamento.objects.filter(
        inicio_processo__date=hoje,
        fim_processo__isnull=False
    ).select_related('soldador', 'componente').order_by('-inicio_processo')
    
    context = {
        'tipos_defeito': tipos_defeito,
        'apontamentos_hoje': apontamentos_hoje,
    }
    
    return render(request, 'qualidade/painel.html', context)

@csrf_exempt
def registrar_defeito(request):
    """Registra defeito em componente"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'})
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        # Implementar lógica de registro de defeito
        return JsonResponse({'success': True, 'message': 'Defeito registrado'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def buscar_apontamentos_soldador(request):
    """Busca apontamentos de um soldador"""
    soldador_id = request.GET.get('soldador_id')
    data_referencia = request.GET.get('data', timezone.now().date().isoformat())
    
    # Implementar lógica de busca
    return JsonResponse({'success': True, 'apontamentos': []})