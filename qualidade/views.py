from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
import json

from core.models import Usuario, Soldador, LogAuditoria
from soldagem.models import Apontamento
from .models import TipoDefeito, Defeito

@login_required
def painel_qualidade(request):
    '''Painel para apontamentos de qualidade'''
    if request.user.tipo_usuario != 'qualidade':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:selecao_soldador')
    
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
    
    return render(request, 'qualidade/painel_qualidade.html', context)

@csrf_exempt
@login_required
def registrar_defeito(request):
    '''Registra defeito em componente'''
    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            with transaction.atomic():
                tipo_defeito = TipoDefeito.objects.get(id=data['tipo_defeito_id'])
                apontamento = Apontamento.objects.get(id=data['apontamento_id'])
                tamanho_mm = data['tamanho_mm']
                observacoes = data.get('observacoes', '')
                
                # Criar defeito
                defeito = Defeito.objects.create(
                    tipo_defeito=tipo_defeito,
                    apontamento=apontamento,
                    soldador=apontamento.soldador,
                    tamanho_mm=tamanho_mm,
                    usuario_qualidade=request.user,
                    observacoes=observacoes
                )
                
                # Log de auditoria
                LogAuditoria.objects.create(
                    usuario=request.user,
                    acao='REGISTRAR_DEFEITO',
                    tabela_afetada='Defeito',
                    registro_id=str(defeito.id),
                    dados_depois={
                        'tipo_defeito': tipo_defeito.nome,
                        'apontamento_id': apontamento.id,
                        'tamanho_mm': float(tamanho_mm),
                        'area_defeito': float(defeito.area_defeito)
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Defeito registrado com sucesso',
                    'defeito_id': defeito.id
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@csrf_exempt
@login_required
def buscar_apontamentos_soldador(request):
    '''Busca apontamentos de um soldador específico'''
    if request.method == 'POST':
        data = json.loads(request.body)
        soldador_id = data.get('soldador_id')
        data_filtro = data.get('data', timezone.now().date().isoformat())
        
        try:
            from datetime import datetime
            data_filtro = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            
            apontamentos = Apontamento.objects.filter(
                soldador_id=soldador_id,
                inicio_processo__date=data_filtro,
                fim_processo__isnull=False
            ).select_related('componente', 'pedido').order_by('-inicio_processo')
            
            apontamentos_data = []
            for apt in apontamentos:
                apontamentos_data.append({
                    'id': apt.id,
                    'componente': apt.componente.nome,
                    'pedido': apt.pedido.numero,
                    'poste': apt.numero_poste_tubo,
                    'inicio': apt.inicio_processo.strftime('%H:%M'),
                    'fim': apt.fim_processo.strftime('%H:%M'),
                    'tempo_real': float(apt.tempo_real or 0),
                    'eficiencia': float(apt.eficiencia_calculada or 0)
                })
            
            return JsonResponse({
                'success': True,
                'apontamentos': apontamentos_data
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})