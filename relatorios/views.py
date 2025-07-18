from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import math

from core.models import Soldador
from soldagem.models import Apontamento, Parada, TipoParada, Modulo, Componente, Turno
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
def relatorio_oee_detalhado(request):
    '''Relatório OEE detalhado com filtros'''
    if request.user.tipo_usuario not in ['admin', 'analista']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', (timezone.now().date() - timedelta(days=7)).isoformat())
    data_fim = request.GET.get('data_fim', timezone.now().date().isoformat())
    soldador_id = request.GET.get('soldador')
    modulo_id = request.GET.get('modulo')
    
    # Converter datas
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Calcular OEE para o período
    oee_resultado = calcular_oee_periodo(data_inicio, data_fim, soldador_id, modulo_id)
    
    # Dados para gráficos
    dados_graficos = preparar_dados_graficos(data_inicio, data_fim, soldador_id, modulo_id)
    
    # Dados para filtros
    soldadores = Soldador.objects.filter(ativo=True).order_by('usuario__nome_completo')
    modulos = Modulo.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'oee_resultado': oee_resultado,
        'dados_graficos': dados_graficos,
        'soldadores': soldadores,
        'modulos': modulos,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'soldador_id': soldador_id,
            'modulo_id': modulo_id,
        }
    }
    
    return render(request, 'relatorios/relatorio_oee_detalhado.html', context)

@login_required
def pontos_melhoria(request):
    '''Relatório de pontos de melhoria'''
    if request.user.tipo_usuario not in ['admin', 'analista']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    data_inicio = request.GET.get('data_inicio', (timezone.now().date() - timedelta(days=7)).isoformat())
    data_fim = request.GET.get('data_fim', timezone.now().date().isoformat())
    soldador_ids = request.GET.getlist('soldadores')
    componente_id = request.GET.get('componente')
    
    # Converter datas
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Query base
    apontamentos = Apontamento.objects.filter(
        inicio_processo__date__gte=data_inicio,
        inicio_processo__date__lte=data_fim,
        fim_processo__isnull=False,
        tempo_real__isnull=False
    ).select_related('soldador', 'componente', 'modulo')
    
    # Aplicar filtros
    if soldador_ids:
        apontamentos = apontamentos.filter(soldador_id__in=soldador_ids)
    
    if componente_id:
        apontamentos = apontamentos.filter(componente_id=componente_id)
    
    # Análise de tempos
    analise_tempos = []
    for apt in apontamentos:
        diferenca_padrao = float(apt.tempo_real) - float(apt.tempo_padrao)
        percentual_diferenca = (diferenca_padrao / float(apt.tempo_padrao)) * 100
        
        analise_tempos.append({
            'soldador': apt.soldador.usuario.nome_completo,
            'componente': apt.componente.nome,
            'modulo': apt.modulo.nome,
            'tempo_padrao': float(apt.tempo_padrao),
            'tempo_real': float(apt.tempo_real),
            'diferenca': diferenca_padrao,
            'percentual_diferenca': percentual_diferenca,
            'eficiencia': float(apt.eficiencia_calculada),
            'data': apt.inicio_processo.strftime('%d/%m/%Y'),
            'hora': apt.inicio_processo.strftime('%H:%M')
        })
    
    # Ordenar por maior diferença
    analise_tempos.sort(key=lambda x: x['diferenca'], reverse=True)
    
    # Dados para filtros
    soldadores = Soldador.objects.filter(ativo=True).order_by('usuario__nome_completo')
    componentes = Componente.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'analise_tempos': analise_tempos[:100],  # Limitar a 100 registros
        'soldadores': soldadores,
        'componentes': componentes,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'soldador_ids': soldador_ids,
            'componente_id': componente_id,
        }
    }
    
    return render(request, 'relatorios/pontos_melhoria.html', context)

@login_required
def relatorio_paradas(request):
    '''Relatório de paradas'''
    if request.user.tipo_usuario not in ['admin', 'analista', 'manutencao']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    data_inicio = request.GET.get('data_inicio', (timezone.now().date() - timedelta(days=7)).isoformat())
    data_fim = request.GET.get('data_fim', timezone.now().date().isoformat())
    soldador_ids = request.GET.getlist('soldadores')
    categoria = request.GET.get('categoria')
    
    # Converter datas
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Query base
    paradas = Parada.objects.filter(
        inicio__date__gte=data_inicio,
        inicio__date__lte=data_fim,
        duracao_minutos__isnull=False
    ).select_related('soldador', 'tipo_parada')
    
    # Aplicar filtros
    if soldador_ids:
        paradas = paradas.filter(soldador_id__in=soldador_ids)
    
    if categoria:
        paradas = paradas.filter(tipo_parada__categoria=categoria)
    
    # Análise de paradas
    analise_paradas = []
    total_tempo_paradas = 0
    
    for parada in paradas:
        duracao_horas = float(parada.duracao_minutos) / 60
        total_tempo_paradas += duracao_horas
        
        analise_paradas.append({
            'soldador': parada.soldador.usuario.nome_completo,
            'tipo_parada': parada.tipo_parada.nome,
            'categoria': parada.tipo_parada.get_categoria_display(),
            'duracao_minutos': float(parada.duracao_minutos),
            'duracao_horas': duracao_horas,
            'penaliza_oee': parada.tipo_parada.penaliza_oee,
            'data': parada.inicio.strftime('%d/%m/%Y'),
            'hora_inicio': parada.inicio.strftime('%H:%M'),
            'hora_fim': parada.fim.strftime('%H:%M') if parada.fim else '',
            'motivo': parada.motivo_detalhado
        })
    
    # Dados para filtros
    soldadores = Soldador.objects.filter(ativo=True).order_by('usuario__nome_completo')
    categorias = TipoParada.CATEGORIAS
    
    context = {
        'analise_paradas': analise_paradas,
        'total_tempo_paradas': total_tempo_paradas,
        'soldadores': soldadores,
        'categorias': categorias,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'soldador_ids': soldador_ids,
            'categoria': categoria,
        }
    }
    
    return render(request, 'relatorios/relatorio_paradas.html', context)

@login_required
def utilizacao_turnos(request):
    '''Análise de utilização considerando múltiplos turnos'''
    if request.user.tipo_usuario not in ['admin', 'analista']:
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    data_inicio = request.GET.get('data_inicio', (timezone.now().date() - timedelta(days=30)).isoformat())
    data_fim = request.GET.get('data_fim', timezone.now().date().isoformat())
    
    # Converter datas
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Calcular utilização atual (1 turno)
    utilizacao_atual = calcular_utilizacao_periodo(data_inicio, data_fim, 1)
    
    # Projeções para 2 e 3 turnos
    utilizacao_2_turnos = calcular_utilizacao_periodo(data_inicio, data_fim, 2)
    utilizacao_3_turnos = calcular_utilizacao_periodo(data_inicio, data_fim, 3)
    
    # Dados para gráfico
    dados_grafico = {
        'cenarios': ['1 Turno (Atual)', '2 Turnos', '3 Turnos'],
        'utilizacao': [
            utilizacao_atual['percentual_utilizacao'],
            utilizacao_2_turnos['percentual_utilizacao'],
            utilizacao_3_turnos['percentual_utilizacao']
        ],
        'horas_disponiveis': [
            utilizacao_atual['horas_disponiveis'],
            utilizacao_2_turnos['horas_disponiveis'],
            utilizacao_3_turnos['horas_disponiveis']
        ],
        'horas_utilizadas': [
            utilizacao_atual['horas_utilizadas'],
            utilizacao_2_turnos['horas_utilizadas'],
            utilizacao_3_turnos['horas_utilizadas']
        ]
    }
    
    context = {
        'utilizacao_atual': utilizacao_atual,
        'utilizacao_2_turnos': utilizacao_2_turnos,
        'utilizacao_3_turnos': utilizacao_3_turnos,
        'dados_grafico': dados_grafico,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    
    return render(request, 'relatorios/utilizacao_turnos.html', context)

# ==================== APIs PARA GRÁFICOS ====================

@csrf_exempt
@login_required
def api_oee_historico(request):
    '''API para dados históricos de OEE'''
    if request.method == 'GET':
        try:
            periodo = int(request.GET.get('periodo', '7'))
            soldador_id = request.GET.get('soldador')
            
            dados = []
            for i in range(periodo):
                data = timezone.now().date() - timedelta(days=i)
                oee_dia = calcular_oee_periodo(data, data, soldador_id)
                
                dados.append({
                    'data': data.strftime('%d/%m'),
                    'utilizacao': float(oee_dia['utilizacao']),
                    'eficiencia': float(oee_dia['eficiencia']),
                    'qualidade': float(oee_dia['qualidade']),
                    'oee': float(oee_dia['oee'])
                })
            
            dados.reverse()  # Ordem cronológica
            
            return JsonResponse({'success': True, 'dados': dados})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@csrf_exempt
@login_required
def api_eficiencia_dispersao(request):
    '''API para gráfico de dispersão de eficiência'''
    if request.method == 'GET':
        try:
            componente_id = request.GET.get('componente')
            periodo = int(request.GET.get('periodo', '7'))
            
            data_inicio = timezone.now().date() - timedelta(days=periodo-1)
            data_fim = timezone.now().date()
            
            apontamentos = Apontamento.objects.filter(
                inicio_processo__date__gte=data_inicio,
                inicio_processo__date__lte=data_fim,
                fim_processo__isnull=False,
                eficiencia_calculada__isnull=False
            ).select_related('soldador', 'componente')
            
            if componente_id:
                apontamentos = apontamentos.filter(componente_id=componente_id)
            
            dados = []
            for apt in apontamentos:
                hora_inicio = apt.inicio_processo.hour + (apt.inicio_processo.minute / 60)
                
                dados.append({
                    'x': hora_inicio,
                    'y': float(apt.eficiencia_calculada),
                    'soldador': apt.soldador.usuario.nome_completo,
                    'componente': apt.componente.nome,
                    'tempo_real': float(apt.tempo_real),
                    'tempo_padrao': float(apt.tempo_padrao),
                    'data': apt.inicio_processo.strftime('%d/%m/%Y')
                })
            
            return JsonResponse({'success': True, 'dados': dados})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@csrf_exempt
@login_required
def api_paradas_categoria(request):
    '''API para gráfico de paradas por categoria'''
    if request.method == 'GET':
        try:
            periodo = int(request.GET.get('periodo', '7'))
            
            data_inicio = timezone.now().date() - timedelta(days=periodo-1)
            data_fim = timezone.now().date()
            
            paradas = Parada.objects.filter(
                inicio__date__gte=data_inicio,
                inicio__date__lte=data_fim,
                duracao_minutos__isnull=False
            ).select_related('tipo_parada')
            
            # Agrupar por categoria
            categorias = {}
            for parada in paradas:
                categoria = parada.tipo_parada.get_categoria_display()
                if categoria not in categorias:
                    categorias[categoria] = 0
                categorias[categoria] += float(parada.duracao_minutos)
            
            dados = {
                'labels': list(categorias.keys()),
                'valores': list(categorias.values()),
                'cores': ['#dc3545', '#ffc107', '#28a745', '#17a2b8', '#6f42c1']
            }
            
            return JsonResponse({'success': True, 'dados': dados})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

# ==================== FUNÇÕES AUXILIARES ====================

def calcular_oee_periodo(data_inicio, data_fim, soldador_id=None, modulo_id=None):
    '''Calcula OEE para um período específico'''
    
    # Query base para apontamentos
    apontamentos = Apontamento.objects.filter(
        inicio_processo__date__gte=data_inicio,
        inicio_processo__date__lte=data_fim,
        fim_processo__isnull=False
    )
    
    if soldador_id:
        apontamentos = apontamentos.filter(soldador_id=soldador_id)
    
    if modulo_id:
        apontamentos = apontamentos.filter(modulo_id=modulo_id)
    
    # Query para paradas
    paradas = Parada.objects.filter(
        inicio__date__gte=data_inicio,
        inicio__date__lte=data_fim,
        duracao_minutos__isnull=False
    )
    
    if soldador_id:
        paradas = paradas.filter(soldador_id=soldador_id)
    
    # Query para defeitos
    defeitos = Defeito.objects.filter(
        data_deteccao__date__gte=data_inicio,
        data_deteccao__date__lte=data_fim
    )
    
    if soldador_id:
        defeitos = defeitos.filter(soldador_id=soldador_id)
    
    # Calcular métricas
    total_apontamentos = apontamentos.count()
    
    if total_apontamentos == 0:
        return {
            'utilizacao': Decimal('0'),
            'eficiencia': Decimal('0'),
            'qualidade': Decimal('100'),
            'oee': Decimal('0'),
            'detalhes': {
                'horas_disponiveis': Decimal('0'),
                'horas_trabalhadas': Decimal('0'),
                'tempo_produtivo': Decimal('0'),
                'tempo_padrao_total': Decimal('0'),
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
    
    # 3. QUALIDADE
    total_defeitos = defeitos.count()
    total_area_defeitos = sum([float(d.area_defeito or 0) for d in defeitos])
    
    # Calcular área total de soldagem
    area_total_soldagem = 0
    for apontamento in apontamentos:
        if apontamento.diametro:
            area_peca = math.pi * float(apontamento.diametro) * 50
            area_total_soldagem += area_peca
    
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

def preparar_dados_graficos(data_inicio, data_fim, soldador_id=None, modulo_id=None):
    '''Prepara dados para gráficos'''
    
    # Dados diários de OEE
    dados_diarios = []
    data_atual = data_inicio
    
    while data_atual <= data_fim:
        oee_dia = calcular_oee_periodo(data_atual, data_atual, soldador_id, modulo_id)
        
        dados_diarios.append({
            'data': data_atual.strftime('%d/%m'),
            'utilizacao': float(oee_dia['utilizacao']),
            'eficiencia': float(oee_dia['eficiencia']),
            'qualidade': float(oee_dia['qualidade']),
            'oee': float(oee_dia['oee'])
        })
        
        data_atual += timedelta(days=1)
    
    return {
        'dados_diarios': dados_diarios,
        'periodo': f"{data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}"
    }