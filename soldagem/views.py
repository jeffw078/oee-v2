# arquivo: soldagem/views.py (SUBSTITUIR as funções existentes)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.hashers import check_password
import json
from datetime import timedelta, datetime

from .models import (
    Usuario, Soldador, Modulo, Componente, Pedido, 
    Turno, Apontamento, TipoParada, Parada, LogAuditoria
)

# ==================== VIEWS PRINCIPAIS ====================

def selecao_soldador(request):
    """Tela inicial de seleção de soldador"""
    # Limpar sessão anterior
    request.session.flush()
    
    soldadores = Soldador.objects.filter(ativo=True).order_by('usuario__nome_completo')
    return render(request, 'soldagem/selecao_soldador.html', {
        'soldadores': soldadores
    })

@csrf_exempt
def login_soldador(request):
    """Login simplificado do soldador"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        soldador_id = data.get('soldador_id')
        senha = data.get('senha')
        
        if not soldador_id or not senha:
            return JsonResponse({'success': False, 'message': 'Soldador e senha são obrigatórios'}, status=400)
        
        soldador = get_object_or_404(Soldador, id=soldador_id, ativo=True)
        
        # Verificar senha simplificada
        if soldador.senha_simplificada != senha:
            return JsonResponse({'success': False, 'message': 'Senha incorreta'}, status=401)
        
        # Login do usuário Django
        login(request, soldador.usuario)
        
        # Salvar na sessão
        request.session['soldador_id'] = soldador.id
        request.session['soldador_nome'] = soldador.usuario.nome_completo
        
        # Criar ou atualizar turno
        hoje = timezone.now().date()
        turno, created = Turno.objects.get_or_create(
            soldador=soldador,
            data_turno=hoje,
            status='ativo',
            defaults={
                'inicio_turno': timezone.now(),
                'horas_disponiveis': 9  # Default 9 horas
            }
        )
        
        # Log de auditoria
        LogAuditoria.objects.create(
            usuario=soldador.usuario,
            acao='LOGIN_SOLDADOR',
            tabela_afetada='Turno',
            registro_id=str(turno.id),
            dados_depois={'soldador': soldador.usuario.nome_completo, 'hora': timezone.now().isoformat()}
        )
        
        return JsonResponse({
            'success': True,
            'redirect_url': '/soldagem/selecao_modulo/'  # Redirecionar para seleção de módulo
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def selecao_modulo(request):
    """Nova view - Tela de seleção de módulo (após login)"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    try:
        soldador = Soldador.objects.get(id=soldador_id, ativo=True)
    except Soldador.DoesNotExist:
        request.session.flush()
        return redirect('soldagem:selecao_soldador')
    
    # Buscar módulos ativos
    modulos = Modulo.objects.filter(ativo=True).order_by('ordem_exibicao')
    
    # Determinar saudação baseada no horário
    hora_atual = timezone.now().hour
    if hora_atual < 12:
        saudacao = "Bom dia"
    elif hora_atual < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"
    
    context = {
        'soldador': soldador,
        'modulos': modulos,
        'saudacao': saudacao,
        'hora_atual': timezone.now()
    }
    
    return render(request, 'soldagem/selecao_modulo.html', context)

@csrf_exempt
def iniciar_modulo(request):
    """Nova API - Inicia processo no módulo selecionado"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'})
    
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return JsonResponse({'success': False, 'message': 'Soldador não autenticado'}, status=401)
    
    try:
        data = json.loads(request.body)
        modulo_id = data.get('modulo_id')
        numero_pedido = data.get('numero_pedido')
        numero_poste = data.get('numero_poste')
        
        # Validações
        if not all([modulo_id, numero_pedido, numero_poste]):
            return JsonResponse({'success': False, 'message': 'Todos os campos são obrigatórios'})
        
        # Salvar na sessão
        request.session['modulo_atual'] = modulo_id
        request.session['pedido_atual'] = numero_pedido
        request.session['poste_atual'] = numero_poste
        
        # Buscar ou criar pedido
        pedido, created = Pedido.objects.get_or_create(
            numero=numero_pedido,
            defaults={'descricao': f'Pedido {numero_pedido}'}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Módulo selecionado com sucesso',
            'redirect_url': '/soldagem/selecao_componente/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def selecao_componente(request):
    """Nova view - Tela de seleção de componente"""
    soldador_id = request.session.get('soldador_id')
    modulo_id = request.session.get('modulo_atual')
    
    if not soldador_id or not modulo_id:
        return redirect('soldagem:selecao_modulo')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    modulo = get_object_or_404(Modulo, id=modulo_id)
    
    # Buscar componentes ativos
    componentes = Componente.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'soldador': soldador,
        'modulo': modulo,
        'componentes': componentes,
        'pedido': request.session.get('pedido_atual'),
        'poste': request.session.get('poste_atual'),
        'hora_atual': timezone.now()
    }
    
    return render(request, 'soldagem/selecao_componente.html', context)

@csrf_exempt
def iniciar_componente(request):
    """Inicia o processo de soldagem do componente"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'})
    
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return JsonResponse({'success': False, 'message': 'Soldador não autenticado'})
    
    try:
        data = json.loads(request.body)
        componente_id = data.get('componente_id')
        diametro = data.get('diametro')  # Opcional, para componentes com diâmetro
        
        soldador = Soldador.objects.get(id=soldador_id)
        componente = Componente.objects.get(id=componente_id)
        modulo_id = request.session.get('modulo_atual')
        pedido_numero = request.session.get('pedido_atual')
        numero_poste = request.session.get('poste_atual')
        
        # Buscar pedido
        pedido = Pedido.objects.get(numero=pedido_numero)
        modulo = Modulo.objects.get(id=modulo_id)
        
        # Criar apontamento
        apontamento = Apontamento.objects.create(
            soldador=soldador,
            modulo=modulo,
            componente=componente,
            pedido=pedido,
            numero_poste_tubo=numero_poste,
            diametro=diametro if componente.considera_diametro else None,
            inicio_processo=timezone.now(),
            tempo_padrao=componente.tempo_padrao
        )
        
        # Salvar ID do apontamento na sessão
        request.session['apontamento_atual'] = apontamento.id
        
        # Log
        LogAuditoria.objects.create(
            usuario=soldador.usuario,
            acao='INICIAR_COMPONENTE',
            tabela_afetada='Apontamento',
            registro_id=str(apontamento.id),
            dados_depois={
                'componente': componente.nome,
                'modulo': modulo.nome,
                'pedido': pedido.numero
            }
        )
        
        return JsonResponse({
            'success': True,
            'apontamento_id': apontamento.id,
            'redirect_url': '/soldagem/processo_soldagem/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def processo_soldagem(request):
    """Nova view - Tela do processo de soldagem em andamento"""
    soldador_id = request.session.get('soldador_id')
    apontamento_id = request.session.get('apontamento_atual')
    
    if not soldador_id or not apontamento_id:
        return redirect('soldagem:selecao_modulo')
    
    try:
        apontamento = Apontamento.objects.get(
            id=apontamento_id,
            soldador_id=soldador_id,
            fim_processo__isnull=True
        )
    except Apontamento.DoesNotExist:
        return redirect('soldagem:selecao_modulo')
    
    context = {
        'apontamento': apontamento,
        'soldador': apontamento.soldador,
        'componente': apontamento.componente,
        'modulo': apontamento.modulo,
        'tempo_decorrido': (timezone.now() - apontamento.inicio_processo).total_seconds()
    }
    
    return render(request, 'soldagem/processo_soldagem.html', context)