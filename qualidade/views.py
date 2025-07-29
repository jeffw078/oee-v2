from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Count, Sum
from decimal import Decimal
import json
import math
from soldagem.models import Usuario, Soldador, Apontamento, Componente
from .models import TipoDefeito, Defeito

@login_required
def painel_qualidade(request):
    """Painel de qualidade para apontamento de defeitos"""
    if request.user.tipo_usuario != 'qualidade':
        messages.error(request, 'Acesso negado ao painel de qualidade')
        return redirect('soldagem:apontamento')
    
    # Buscar dados necessários
    tipos_defeito = TipoDefeito.objects.filter(ativo=True).order_by('nome')
    
    # Buscar apontamentos do dia atual que podem receber defeitos
    hoje = timezone.now().date()
    apontamentos_disponiveis = Apontamento.objects.filter(
        inicio_processo__date=hoje,
        fim_processo__isnull=False  # Apenas apontamentos finalizados
    ).select_related('soldador__usuario', 'componente', 'modulo').order_by('-fim_processo')
    
    context = {
        'tipos_defeito': tipos_defeito,
        'apontamentos_disponiveis': apontamentos_disponiveis,
        'usuario_qualidade': request.user,
    }
    
    return render(request, 'qualidade/painel_qualidade.html', context)

@csrf_exempt
@login_required
def registrar_defeito(request):
    """Registra um defeito de qualidade com cálculo correto de área"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'})
    
    if request.user.tipo_usuario != 'qualidade':
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    try:
        dados = json.loads(request.body)
        
        # Validar dados obrigatórios
        tipo_defeito_id = dados.get('tipo_defeito_id')
        apontamento_id = dados.get('apontamento_id')
        tamanho_mm = dados.get('tamanho_mm')
        observacoes = dados.get('observacoes', '')
        
        if not all([tipo_defeito_id, apontamento_id, tamanho_mm]):
            return JsonResponse({'success': False, 'message': 'Dados obrigatórios não informados'})
        
        # Buscar objetos
        tipo_defeito = TipoDefeito.objects.get(id=tipo_defeito_id, ativo=True)
        apontamento = Apontamento.objects.get(id=apontamento_id)
        
        # CORREÇÃO PROBLEMA 3 - Cálculo correto da área de soldagem
        area_solda_componente = calcular_area_soldagem_componente(apontamento)
        
        # Calcular área do defeito (círculo)
        raio_defeito = float(tamanho_mm) / 2
        area_defeito = math.pi * (raio_defeito ** 2)
        
        # Calcular percentual de penalização
        percentual_defeito = (area_defeito / area_solda_componente) * 100 if area_solda_componente > 0 else 0
        
        # Criar registro de defeito
        defeito = Defeito.objects.create(
            tipo_defeito=tipo_defeito,
            apontamento=apontamento,
            soldador=apontamento.soldador,
            tamanho_mm=Decimal(str(tamanho_mm)),
            area_defeito=Decimal(str(area_defeito)),
            usuario_qualidade=request.user,
            observacoes=observacoes
        )
        
        # Calcular impacto na qualidade
        qualidade_final = max(0, 100 - percentual_defeito)
        
        return JsonResponse({
            'success': True,
            'message': 'Defeito registrado com sucesso',
            'defeito_id': defeito.id,
            'calculos': {
                'area_solda_componente': float(area_solda_componente),
                'area_defeito': float(area_defeito),
                'percentual_defeito': round(percentual_defeito, 2),
                'qualidade_final': round(qualidade_final, 2),
                'penalizacao': round(percentual_defeito, 2)
            }
        })
        
    except TipoDefeito.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Tipo de defeito não encontrado'})
    except Apontamento.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Apontamento não encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro interno: {str(e)}'})

def calcular_area_soldagem_componente(apontamento):
    """
    Calcula a área total de soldagem para um componente específico
    CORREÇÃO PROBLEMA 3 - Área baseada no componente real
    """
    componente = apontamento.componente
    
    # Definir áreas padrão de soldagem por componente (em mm²)
    areas_componentes = {
        'OLHAL DE IÇAMENTO': 30000,  # 300cm² = 30000mm²
        'FAIS': 25000,
        'FAIB': 28000,
        'FAES': 22000,
        'FAIE': 32000,
        'ATERRAMENTO': 15000,
        'OLHAL LINHA DE VIDA': 18500,
        'ESCADAS': 85000,
        'MÃO FRANCESA': 65000,
        'OLHAIS DE FASE': 33800,
        'APOIO DE PÉ E MÃO': 6000,
        'CHAPA DA CRUZETA': 45000,
        'BASE ISOLADORA': 38000,
        'ANTIGIRO': 20000,
        'CHAPA DE SACRIFÍCIO': 12000,
    }
    
    # Buscar área específica do componente
    area_base = areas_componentes.get(componente.nome.upper(), 20000)  # Área padrão: 20000mm²
    
    # Se componente considera diâmetro, ajustar área proporcionalmente
    if componente.considera_diametro and apontamento.diametro:
        # Fator de correção baseado no diâmetro
        diametro_padrao = 500  # mm (diâmetro de referência)
        fator_diametro = float(apontamento.diametro) / diametro_padrao
        area_final = area_base * fator_diametro
    else:
        area_final = area_base
    
    return area_final

@login_required
def api_apontamentos_dia(request):
    """API para buscar apontamentos do dia para seleção"""
    if request.user.tipo_usuario != 'qualidade':
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    hoje = timezone.now().date()
    soldador_id = request.GET.get('soldador_id')
    
    apontamentos = Apontamento.objects.filter(
        inicio_processo__date=hoje,
        fim_processo__isnull=False
    ).select_related('soldador__usuario', 'componente', 'modulo')
    
    if soldador_id:
        apontamentos = apontamentos.filter(soldador_id=soldador_id)
    
    dados = []
    for apt in apontamentos:
        # Calcular defeitos já registrados para este apontamento
        defeitos_existentes = Defeito.objects.filter(apontamento=apt)
        total_area_defeitos = sum([float(d.area_defeito or 0) for d in defeitos_existentes])
        
        area_solda = calcular_area_soldagem_componente(apt)
        percentual_defeitos = (total_area_defeitos / area_solda) * 100 if area_solda > 0 else 0
        qualidade_atual = max(0, 100 - percentual_defeitos)
        
        dados.append({
            'id': apt.id,
            'soldador': apt.soldador.usuario.nome_completo,
            'modulo': apt.modulo.nome,
            'componente': apt.componente.nome,
            'inicio': apt.inicio_processo.strftime('%H:%M'),
            'fim': apt.fim_processo.strftime('%H:%M') if apt.fim_processo else '-',
            'diametro': float(apt.diametro) if apt.diametro else None,
            'area_soldagem': float(area_solda),
            'defeitos_existentes': defeitos_existentes.count(),
            'qualidade_atual': round(qualidade_atual, 2),
            'pode_adicionar_defeito': qualidade_atual > 0
        })
    
    return JsonResponse({'success': True, 'apontamentos': dados})

@login_required
def relatorio_qualidade(request):
    """Relatório de qualidade detalhado"""
    if request.user.tipo_usuario not in ['admin', 'analista', 'qualidade']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', timezone.now().date())
    data_fim = request.GET.get('data_fim', timezone.now().date())
    soldador_id = request.GET.get('soldador_id')
    
    # Buscar defeitos no período
    defeitos = Defeito.objects.filter(
        data_deteccao__date__gte=data_inicio,
        data_deteccao__date__lte=data_fim
    ).select_related('tipo_defeito', 'apontamento__soldador__usuario', 'apontamento__componente')
    
    if soldador_id:
        defeitos = defeitos.filter(apontamento__soldador_id=soldador_id)
    
    # Estatísticas gerais
    total_defeitos = defeitos.count()
    tipos_mais_frequentes = defeitos.values('tipo_defeito__nome').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Calcular impacto médio na qualidade
    impactos_qualidade = []
    for defeito in defeitos:
        area_solda = calcular_area_soldagem_componente(defeito.apontamento)
        percentual = (float(defeito.area_defeito or 0) / area_solda) * 100 if area_solda > 0 else 0
        impactos_qualidade.append(percentual)
    
    impacto_medio = sum(impactos_qualidade) / len(impactos_qualidade) if impactos_qualidade else 0
    
    context = {
        'defeitos': defeitos,
        'total_defeitos': total_defeitos,
        'tipos_mais_frequentes': tipos_mais_frequentes,
        'impacto_medio_qualidade': round(impacto_medio, 2),
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'soldadores': Soldador.objects.filter(ativo=True),
        'soldador_selecionado': soldador_id,
    }
    
    return render(request, 'qualidade/relatorio_qualidade.html', context)