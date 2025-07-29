from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q, Min, Max
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import math
import csv
from soldagem.models import Apontamento, Parada, TipoParada, Modulo, Componente, Turno, Soldador
from qualidade.models import Defeito

@login_required
def dashboard_principal(request):
    '''Dashboard principal com indicadores OEE'''
    if request.user.tipo_usuario not in ['admin', 'analista', 'qualidade', 'manutencao']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    hoje = timezone.now().date()
    
    # Calcular OEE do dia atual
    oee_hoje = calcular_oee_periodo(hoje, hoje)
    
    # Indicadores rápidos
    apontamentos_hoje = Apontamento.objects.filter(
        inicio_processo__date=hoje,
        fim_processo__isnull=False
    ).count()
    
    defeitos_hoje = Defeito.objects.filter(data_deteccao__date=hoje).count()
    paradas_hoje = Parada.objects.filter(inicio__date=hoje).count()
    
    # Soldadores ativos
    soldadores_ativos = Turno.objects.filter(
        data_turno=hoje,
        status='ativo'
    ).count()
    
    # Módulos soldados hoje
    modulos_soldados = Apontamento.objects.filter(
        inicio_processo__date=hoje,
        fim_processo__isnull=False
    ).values('numero_poste_tubo').distinct().count()
    
    context = {
        'oee_hoje': oee_hoje,
        'indicadores': {
            'total_apontamentos': apontamentos_hoje,
            'total_defeitos': defeitos_hoje,
            'total_paradas': paradas_hoje,
            'soldadores_ativos': soldadores_ativos,
            'modulos_soldados': modulos_soldados,
        },
        'data_referencia': hoje,
    }
    
    return render(request, 'relatorios/dashboard_principal.html', context)

@login_required
def pontos_melhoria(request):
    '''Relatório de pontos de melhoria'''
    if request.user.tipo_usuario not in ['admin', 'analista']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', (timezone.now() - timedelta(days=7)).date())
    data_fim = request.GET.get('data_fim', timezone.now().date())
    soldadores_selecionados = request.GET.getlist('soldadores')
    componente_id = request.GET.get('componente_id')
    
    # Base da consulta
    apontamentos = Apontamento.objects.filter(
        inicio_processo__date__gte=data_inicio,
        inicio_processo__date__lte=data_fim,
        fim_processo__isnull=False
    ).select_related('soldador__usuario', 'componente', 'modulo')
    
    if soldadores_selecionados:
        apontamentos = apontamentos.filter(soldador_id__in=soldadores_selecionados)
    if componente_id:
        apontamentos = apontamentos.filter(componente_id=componente_id)
    
    # Análise de tempos vs padrão
    analise_tempos = []
    for apontamento in apontamentos:
        if apontamento.tempo_real and apontamento.tempo_padrao:
            tempo_real_min = float(apontamento.tempo_real)
            tempo_padrao_min = float(apontamento.tempo_padrao)
            diferenca = tempo_real_min - tempo_padrao_min
            percentual_diferenca = (diferenca / tempo_padrao_min) * 100 if tempo_padrao_min > 0 else 0
            
            analise_tempos.append({
                'apontamento': apontamento,
                'tempo_real': tempo_real_min,
                'tempo_padrao': tempo_padrao_min,
                'diferenca': diferenca,
                'percentual_diferenca': percentual_diferenca,
                'acima_padrao': diferenca > 0
            })
    
    # Ordenar por maior diferença (piores performances)
    analise_tempos.sort(key=lambda x: x['percentual_diferenca'], reverse=True)
    
    # Estatísticas por soldador
    stats_soldadores = {}
    for item in analise_tempos:
        soldador = item['apontamento'].soldador.usuario.nome_completo
        if soldador not in stats_soldadores:
            stats_soldadores[soldador] = {
                'total_apontamentos': 0,
                'tempo_total_diferenca': 0,
                'maior_diferenca': 0,
                'apontamentos_acima_padrao': 0
            }
        
        stats_soldadores[soldador]['total_apontamentos'] += 1
        stats_soldadores[soldador]['tempo_total_diferenca'] += item['diferenca']
        stats_soldadores[soldador]['maior_diferenca'] = max(
            stats_soldadores[soldador]['maior_diferenca'], 
            item['percentual_diferenca']
        )
        if item['acima_padrao']:
            stats_soldadores[soldador]['apontamentos_acima_padrao'] += 1
    
    # Estatísticas por componente
    stats_componentes = {}
    for item in analise_tempos:
        componente = item['apontamento'].componente.nome
        if componente not in stats_componentes:
            stats_componentes[componente] = {
                'total_apontamentos': 0,
                'tempo_medio_diferenca': 0,
                'total_diferenca': 0
            }
        
        stats_componentes[componente]['total_apontamentos'] += 1
        stats_componentes[componente]['total_diferenca'] += item['diferenca']
    
    for comp in stats_componentes:
        if stats_componentes[comp]['total_apontamentos'] > 0:
            stats_componentes[comp]['tempo_medio_diferenca'] = (
                stats_componentes[comp]['total_diferenca'] / 
                stats_componentes[comp]['total_apontamentos']
            )
    
    context = {
        'analise_tempos': analise_tempos[:50],  # Top 50 piores
        'stats_soldadores': stats_soldadores,
        'stats_componentes': stats_componentes,
        'soldadores': Soldador.objects.filter(ativo=True),
        'componentes': Componente.objects.filter(ativo=True),
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'soldadores_selecionados': soldadores_selecionados,
        'componente_selecionado': componente_id,
    }
    
    return render(request, 'relatorios/pontos_melhoria.html', context)

@login_required
def relatorio_paradas(request):
    '''Relatório detalhado de paradas'''
    if request.user.tipo_usuario not in ['admin', 'analista']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', (timezone.now() - timedelta(days=7)).date())
    data_fim = request.GET.get('data_fim', timezone.now().date())
    soldadores_selecionados = request.GET.getlist('soldadores')
    categoria = request.GET.get('categoria')
    
    # Base da consulta
    paradas = Parada.objects.filter(
        inicio__date__gte=data_inicio,
        inicio__date__lte=data_fim,
        fim__isnull=False
    ).select_related('tipo_parada', 'soldador__usuario')
    
    if soldadores_selecionados:
        paradas = paradas.filter(soldador_id__in=soldadores_selecionados)
    if categoria:
        paradas = paradas.filter(tipo_parada__categoria=categoria)
    
    # Análise por tipo de parada
    paradas_por_tipo = paradas.values('tipo_parada__nome', 'tipo_parada__categoria', 'tipo_parada__penaliza_oee').annotate(
        total_ocorrencias=Count('id'),
        tempo_total_minutos=Sum('duracao_minutos'),
        tempo_medio_minutos=Avg('duracao_minutos')
    ).order_by('-tempo_total_minutos')
    
    # Análise por soldador
    paradas_por_soldador = paradas.values('soldador__usuario__nome_completo').annotate(
        total_ocorrencias=Count('id'),
        tempo_total_minutos=Sum('duracao_minutos'),
        tempo_medio_minutos=Avg('duracao_minutos')
    ).order_by('-tempo_total_minutos')
    
    # Análise por dia
    paradas_por_dia = paradas.extra({
        'data': 'DATE(inicio)'
    }).values('data').annotate(
        total_ocorrencias=Count('id'),
        tempo_total_minutos=Sum('duracao_minutos')
    ).order_by('data')
    
    # Top 10 maiores paradas
    maiores_paradas = paradas.order_by('-duracao_minutos')[:10]
    
    # Estatísticas gerais
    total_paradas = paradas.count()
    tempo_total_paradas = paradas.aggregate(Sum('duracao_minutos'))['duracao_minutos__sum'] or 0
    tempo_medio_parada = paradas.aggregate(Avg('duracao_minutos'))['duracao_minutos__avg'] or 0
    
    # Paradas que penalizam vs não penalizam OEE
    paradas_penalizantes = paradas.filter(tipo_parada__penaliza_oee=True)
    tempo_paradas_penalizantes = paradas_penalizantes.aggregate(Sum('duracao_minutos'))['duracao_minutos__sum'] or 0
    
    context = {
        'paradas_por_tipo': paradas_por_tipo,
        'paradas_por_soldador': paradas_por_soldador,
        'paradas_por_dia': paradas_por_dia,
        'maiores_paradas': maiores_paradas,
        'estatisticas': {
            'total_paradas': total_paradas,
            'tempo_total_paradas': round(tempo_total_paradas / 60, 2),  # Converter para horas
            'tempo_medio_parada': round(tempo_medio_parada, 1),
            'tempo_paradas_penalizantes': round(tempo_paradas_penalizantes / 60, 2),
            'percentual_penalizante': round((tempo_paradas_penalizantes / tempo_total_paradas * 100), 1) if tempo_total_paradas > 0 else 0
        },
        'soldadores': Soldador.objects.filter(ativo=True),
        'categorias': TipoParada.CATEGORIA_CHOICES,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'soldadores_selecionados': soldadores_selecionados,
        'categoria_selecionada': categoria,
    }
    
    return render(request, 'relatorios/relatorio_paradas.html', context)

@login_required
def utilizacao_turnos(request):
    '''Gráfico de utilização comparando 1, 2 e 3 turnos'''
    if request.user.tipo_usuario not in ['admin', 'analista']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', (timezone.now() - timedelta(days=30)).date())
    data_fim = request.GET.get('data_fim', timezone.now().date())
    
    # Calcular utilização atual (considerando 1 turno de 8h)
    utilizacao_atual = calcular_utilizacao_periodo(data_inicio, data_fim, 1)
    utilizacao_2_turnos = calcular_utilizacao_periodo(data_inicio, data_fim, 2)
    utilizacao_3_turnos = calcular_utilizacao_periodo(data_inicio, data_fim, 3)
    
    # Dados para gráfico de utilização por dia
    dados_diarios = []
    data_atual = data_inicio
    
    while data_atual <= data_fim:
        # Horas realmente trabalhadas no dia
        apontamentos_dia = Apontamento.objects.filter(
            inicio_processo__date=data_atual,
            fim_processo__isnull=False
        )
        
        horas_trabalhadas = sum([
            float(a.tempo_real) for a in apontamentos_dia if a.tempo_real
        ]) / 60
        
        dados_diarios.append({
            'data': data_atual.strftime('%d/%m'),
            'horas_trabalhadas': round(horas_trabalhadas, 2),
            'disponivel_1_turno': 8,
            'disponivel_2_turnos': 16,
            'disponivel_3_turnos': 24,
            'utilizacao_1_turno': round((horas_trabalhadas / 8 * 100), 1) if horas_trabalhadas <= 8 else 100,
            'utilizacao_2_turnos': round((horas_trabalhadas / 16 * 100), 1) if horas_trabalhadas <= 16 else 100,
            'utilizacao_3_turnos': round((horas_trabalhadas / 24 * 100), 1) if horas_trabalhadas <= 24 else 100,
        })
        
        data_atual += timedelta(days=1)
    
    # Projeções de melhoria
    dias_periodo = (data_fim - data_inicio).days + 1
    horas_totais_trabalhadas = utilizacao_atual['horas_utilizadas']
    
    potencial_2_turnos = (dias_periodo * 16) - horas_totais_trabalhadas
    potencial_3_turnos = (dias_periodo * 24) - horas_totais_trabalhadas
    
    context = {
        'utilizacao_atual': utilizacao_atual,
        'utilizacao_2_turnos': utilizacao_2_turnos,
        'utilizacao_3_turnos': utilizacao_3_turnos,
        'dados_diarios': dados_diarios,
        'projecoes': {
            'potencial_2_turnos': round(potencial_2_turnos, 1),
            'potencial_3_turnos': round(potencial_3_turnos, 1),
            'aumento_capacidade_2_turnos': 100,  # 2x
            'aumento_capacidade_3_turnos': 200,  # 3x
        },
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'relatorios/utilizacao_turnos.html', context)

def calcular_oee_periodo(data_inicio, data_fim, soldador_id=None):
    """Calcula OEE para um período específico"""
    
    # Filtrar apontamentos
    apontamentos = Apontamento.objects.filter(
        inicio_processo__date__gte=data_inicio,
        inicio_processo__date__lte=data_fim,
        fim_processo__isnull=False
    )
    
    if soldador_id:
        apontamentos = apontamentos.filter(soldador_id=soldador_id)
    
    # Filtrar paradas e defeitos
    paradas = Parada.objects.filter(
        inicio__date__gte=data_inicio,
        inicio__date__lte=data_fim,
        fim__isnull=False
    )
    
    defeitos = Defeito.objects.filter(
        data_deteccao__date__gte=data_inicio,
        data_deteccao__date__lte=data_fim
    )
    
    if soldador_id:
        paradas = paradas.filter(soldador_id=soldador_id)
        defeitos = defeitos.filter(soldador_id=soldador_id)
    
    total_apontamentos = apontamentos.count()
    
    if total_apontamentos == 0:
        return {
            'utilizacao': 0,
            'eficiencia': 0,
            'qualidade': 100,
            'oee': 0,
            'detalhes': {
                'horas_disponiveis': 0,
                'horas_trabalhadas': 0,
                'tempo_produtivo': 0,
                'tempo_padrao_total': 0,
                'total_apontamentos': 0,
                'total_defeitos': 0,
                'total_paradas': 0
            }
        }
    
    # 1. UTILIZAÇÃO
    dias_periodo = (data_fim - data_inicio).days + 1
    horas_disponiveis = Decimal(str(dias_periodo * 8))
    
    # Tempo total de paradas que penalizam OEE
    tempo_paradas_penalizantes = sum([
        p.duracao_minutos for p in paradas 
        if p.tipo_parada.penaliza_oee and p.duracao_minutos
    ]) / 60
    
    horas_trabalhadas = horas_disponiveis - Decimal(str(tempo_paradas_penalizantes))
    utilizacao = (horas_trabalhadas / horas_disponiveis * 100) if horas_disponiveis > 0 else Decimal('0')
    
    # 2. EFICIÊNCIA
    tempo_real_total = sum([
        float(a.tempo_real) for a in apontamentos if a.tempo_real
    ]) / 60
    
    tempo_padrao_total = sum([
        float(a.tempo_padrao) for a in apontamentos
    ]) / 60
    
    eficiencia = (Decimal(str(tempo_padrao_total)) / Decimal(str(tempo_real_total)) * 100) if tempo_real_total > 0 else Decimal('0')
    
    # 3. QUALIDADE (CORRIGIDO - PROBLEMA 3)
    total_defeitos = defeitos.count()
    total_area_defeitos = sum([float(d.area_defeito or 0) for d in defeitos])
    
    # Calcular área total de soldagem baseada nos componentes
    area_total_soldagem = 0
    for apontamento in apontamentos:
        area_componente = calcular_area_soldagem_componente(apontamento)
        area_total_soldagem += area_componente
    
    if area_total_soldagem > 0:
        percentual_defeito = (total_area_defeitos / area_total_soldagem) * 100
        qualidade = max(Decimal('0'), 100 - Decimal(str(percentual_defeito)))
    else:
        qualidade = Decimal('100')
    
    # 4. OEE FINAL
    oee = (utilizacao * eficiencia * qualidade) / 10000
    
    return {
        'utilizacao': round(utilizacao, 2),
        'eficiencia': round(eficiencia, 2),
        'qualidade': round(qualidade, 2),
        'oee': round(oee, 2),
        'detalhes': {
            'horas_disponiveis': round(horas_disponiveis, 2),
            'horas_trabalhadas': round(horas_trabalhadas, 2),
            'tempo_produtivo': round(Decimal(str(tempo_real_total)), 2),
            'tempo_padrao_total': round(Decimal(str(tempo_padrao_total)), 2),
            'total_apontamentos': total_apontamentos,
            'total_defeitos': total_defeitos,
            'total_paradas': paradas.count()
        }
    }

def calcular_area_soldagem_componente(apontamento):
    """Função auxiliar importada da qualidade"""
    from qualidade.views import calcular_area_soldagem_componente as calc_area
    return calc_area(apontamento)

def calcular_utilizacao_periodo(data_inicio, data_fim, num_turnos):
    '''Calcula utilização considerando múltiplos turnos'''
    
    dias_periodo = (data_fim - data_inicio).days + 1
    horas_disponiveis_total = dias_periodo * 8 * num_turnos
    
    # Horas realmente utilizadas (baseado em apontamentos)
    apontamentos = Apontamento.objects.filter(
        inicio_processo__date__gte=data_inicio,
        inicio_processo__date__lte=data_fim,
        fim_processo__isnull=False
    )
    
    horas_utilizadas = sum([
        float(a.tempo_real) for a in apontamentos if a.tempo_real
    ]) / 60
    
    percentual_utilizacao = (horas_utilizadas / horas_disponiveis_total * 100) if horas_disponiveis_total > 0 else 0
    
    return {
        'horas_disponiveis': horas_disponiveis_total,
        'horas_utilizadas': horas_utilizadas,
        'percentual_utilizacao': round(percentual_utilizacao, 2),
        'potencial_melhoria': round(100 - percentual_utilizacao, 2)
    }

# APIs para gráficos
@login_required
def api_oee_historico(request):
    '''API para dados históricos de OEE'''
    periodo = int(request.GET.get('periodo', 7))
    
    dados = []
    data_atual = timezone.now().date() - timedelta(days=periodo-1)
    
    for i in range(periodo):
        oee_dia = calcular_oee_periodo(data_atual, data_atual)
        dados.append({
            'data': data_atual.strftime('%d/%m'),
            'oee': float(oee_dia['oee']),
            'utilizacao': float(oee_dia['utilizacao']),
            'eficiencia': float(oee_dia['eficiencia']),
            'qualidade': float(oee_dia['qualidade'])
        })
        data_atual += timedelta(days=1)
    
    return JsonResponse({'success': True, 'dados': dados})

@login_required
def api_eficiencia_dispersao(request):
    '''API para gráfico de dispersão de eficiência'''
    periodo = int(request.GET.get('periodo', 30))
    
    data_inicio = timezone.now().date() - timedelta(days=periodo-1)
    data_fim = timezone.now().date()
    
    apontamentos = Apontamento.objects.filter(
        inicio_processo__date__gte=data_inicio,
        inicio_processo__date__lte=data_fim,
        fim_processo__isnull=False,
        tempo_real__isnull=False,
        tempo_padrao__isnull=False
    ).select_related('soldador__usuario', 'componente')
    
    dados = []
    for apt in apontamentos:
        if apt.tempo_real and apt.tempo_padrao:
            eficiencia = (float(apt.tempo_padrao) / float(apt.tempo_real)) * 100
            dados.append({
                'x': apt.inicio_processo.strftime('%d/%m'),
                'y': round(eficiencia, 1),
                'soldador': apt.soldador.usuario.nome_completo,
                'componente': apt.componente.nome,
                'tempo_real': float(apt.tempo_real),
                'tempo_padrao': float(apt.tempo_padrao)
            })
    
    return JsonResponse({'success': True, 'dados': dados})

@login_required
def api_paradas_categoria(request):
    '''API para gráfico de paradas por categoria'''
    periodo = int(request.GET.get('periodo', 7))
    
    data_inicio = timezone.now().date() - timedelta(days=periodo-1)
    data_fim = timezone.now().date()
    
    paradas = Parada.objects.filter(
        inicio__date__gte=data_inicio,
        inicio__date__lte=data_fim,
        fim__isnull=False
    ).values('tipo_parada__categoria').annotate(
        total_tempo=Sum('duracao_minutos'),
        total_ocorrencias=Count('id')
    )
    
    dados = {
        'categorias': [],
        'tempos': [],
        'ocorrencias': []
    }
    
    for parada in paradas:
        dados['categorias'].append(parada['tipo_parada__categoria'].title())
        dados['tempos'].append(round((parada['total_tempo'] or 0) / 60, 2))  # Converter para horas
        dados['ocorrencias'].append(parada['total_ocorrencias'])
    
    return JsonResponse({'success': True, 'dados': dados})