# qualidade/views.py - VERSÃO COMPLETA

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
import json
import math

from core.models import Usuario, Soldador, LogAuditoria
from soldagem.models import Apontamento
from .models import TipoDefeito, Defeito

@login_required
def painel_qualidade(request):
    '''Painel para apontamentos de qualidade'''
    if request.user.tipo_usuario != 'qualidade':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:selecao_soldador')
    
    tipos_defeito = TipoDefeito.objects.filter(ativo=True).order_by('nome')
    
    # Buscar apontamentos do dia atual
    hoje = timezone.now().date()
    apontamentos_hoje = Apontamento.objects.filter(
        inicio_processo__date=hoje,
        fim_processo__isnull=False
    ).select_related('soldador', 'componente', 'modulo').order_by('-inicio_processo')
    
    context = {
        'tipos_defeito': tipos_defeito,
        'apontamentos_hoje': apontamentos_hoje,
    }
    
    return render(request, 'qualidade/painel_qualidade.html', context)

@csrf_exempt
@login_required
def registrar_defeito(request):
    '''Registra defeito em componente'''
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    if request.user.tipo_usuario != 'qualidade':
        return JsonResponse({'success': False, 'message': 'Acesso negado'}, status=403)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        tipo_defeito_id = data.get('tipo_defeito_id')
        apontamento_id = data.get('apontamento_id')
        tamanho_mm = data.get('tamanho_mm')
        observacoes = data.get('observacoes', '')
        
        with transaction.atomic():
            tipo_defeito = TipoDefeito.objects.get(id=tipo_defeito_id, ativo=True)
            apontamento = Apontamento.objects.get(id=apontamento_id)
            
            # Calcular área do defeito (simplificado como círculo)
            raio = float(tamanho_mm) / 2
            area_defeito = math.pi * (raio ** 2)
            
            # Criar defeito
            defeito = Defeito.objects.create(
                tipo_defeito=tipo_defeito,
                apontamento=apontamento,
                soldador=apontamento.soldador,
                tamanho_mm=tamanho_mm,
                area_defeito=area_defeito,
                data_deteccao=timezone.now(),
                usuario_qualidade=request.user,
                observacoes=observacoes
            )
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario=request.user,
                acao='REGISTRAR_DEFEITO',
                tabela_afetada='Defeito',
                registro_id=defeito.id,
                dados_depois={
                    'tipo_defeito': tipo_defeito.nome,
                    'soldador': apontamento.soldador.usuario.nome_completo,
                    'componente': apontamento.componente.nome,
                    'tamanho_mm': float(tamanho_mm),
                    'area_defeito': area_defeito
                }
            )
            
            return JsonResponse({
                'success': True,
                'defeito_id': defeito.id,
                'area_defeito': area_defeito,
                'message': 'Defeito registrado com sucesso'
            })
            
    except TipoDefeito.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Tipo de defeito não encontrado'}, status=404)
    except Apontamento.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Apontamento não encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def buscar_apontamentos_soldador(request):
    '''Busca apontamentos de um soldador específico para o dia'''
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        soldador_id = request.GET.get('soldador_id')
        data_referencia = request.GET.get('data', timezone.now().date().isoformat())
        
        # Converter data
        from datetime import datetime
        data_referencia = datetime.strptime(data_referencia, '%Y-%m-%d').date()
        
        apontamentos = Apontamento.objects.filter(
            soldador_id=soldador_id,
            inicio_processo__date=data_referencia,
            fim_processo__isnull=False
        ).select_related('componente', 'modulo').order_by('-inicio_processo')
        
        apontamentos_data = []
        for apt in apontamentos:
            apontamentos_data.append({
                'id': apt.id,
                'componente_nome': apt.componente.nome,
                'modulo_nome': apt.modulo.nome,
                'numero_poste_tubo': apt.numero_poste_tubo,
                'diametro': float(apt.diametro) if apt.diametro else None,
                'inicio_processo': apt.inicio_processo.strftime('%H:%M:%S'),
                'fim_processo': apt.fim_processo.strftime('%H:%M:%S'),
                'tempo_real': float(apt.tempo_real) if apt.tempo_real else 0,
                'tempo_padrao': float(apt.tempo_padrao),
                'eficiencia': float(apt.eficiencia_calculada) if apt.eficiencia_calculada else 0
            })
        
        return JsonResponse({
            'success': True,
            'apontamentos': apontamentos_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt  
def calcular_qualidade_tempo_real(request):
    '''Calcula índice de qualidade em tempo real'''
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        apontamento_id = request.GET.get('apontamento_id')
        tamanho_defeito = float(request.GET.get('tamanho_defeito', 0))
        
        apontamento = Apontamento.objects.get(id=apontamento_id)
        
        # Calcular área do defeito
        raio = tamanho_defeito / 2
        area_defeito = math.pi * (raio ** 2)
        
        # Calcular área total da peça (baseado no diâmetro)
        if apontamento.diametro:
            # Área aproximada baseada no diâmetro e comprimento médio
            comprimento_medio = 50  # cm (pode ser configurável)
            area_total_peca = math.pi * float(apontamento.diametro) * comprimento_medio
        else:
            # Área padrão para componentes sem diâmetro
            area_total_peca = 1000  # cm²
        
        # Calcular percentual de defeito
        percentual_defeito = (area_defeito / area_total_peca) * 100
        
        # Índice de qualidade (100% - percentual de defeito)
        indice_qualidade = max(0, 100 - percentual_defeito)
        
        return JsonResponse({
            'success': True,
            'area_defeito': round(area_defeito, 2),
            'area_total_peca': round(area_total_peca, 2),
            'percentual_defeito': round(percentual_defeito, 2),
            'indice_qualidade': round(indice_qualidade, 2)
        })
        
    except Apontamento.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Apontamento não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)