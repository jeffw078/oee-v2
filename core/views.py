from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
import json

from .models import Usuario, Soldador, Modulo, Componente, ConfiguracaoSistema, LogAuditoria
from soldagem.models import Apontamento, TipoParada, Pedido
from qualidade.models import TipoDefeito

@login_required
def painel_admin(request):
    '''Painel administrativo principal'''
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:selecao_soldador')
    
    # Estatísticas gerais
    total_soldadores = Soldador.objects.filter(ativo=True).count()
    total_apontamentos = Apontamento.objects.count()
    total_pedidos = Pedido.objects.count()
    
    # Apontamentos recentes
    apontamentos_recentes = Apontamento.objects.select_related(
        'soldador', 'componente', 'pedido'
    ).order_by('-data_criacao')[:10]
    
    # Logs de auditoria recentes
    logs_recentes = LogAuditoria.objects.select_related('usuario').order_by('-timestamp')[:10]
    
    context = {
        'total_soldadores': total_soldadores,
        'total_apontamentos': total_apontamentos,
        'total_pedidos': total_pedidos,
        'apontamentos_recentes': apontamentos_recentes,
        'logs_recentes': logs_recentes,
    }
    
    return render(request, 'admin/painel_admin.html', context)

@login_required
def gerenciar_soldadores(request):
    '''Gerenciar soldadores'''
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:selecao_soldador')
    
    if request.method == 'POST':
        # Criar/editar soldador
        nome_completo = request.POST.get('nome_completo')
        username = request.POST.get('username')
        senha_simplificada = request.POST.get('senha_simplificada')
        soldador_id = request.POST.get('soldador_id')
        
        try:
            with transaction.atomic():
                if soldador_id:
                    # Editar
                    soldador = Soldador.objects.get(id=soldador_id)
                    soldador.usuario.nome_completo = nome_completo
                    soldador.usuario.username = username
                    soldador.usuario.save()
                    soldador.senha_simplificada = senha_simplificada
                    soldador.save()
                    
                    messages.success(request, 'Soldador atualizado com sucesso')
                else:
                    # Criar
                    usuario = Usuario.objects.create_user(
                        username=username,
                        nome_completo=nome_completo,
                        tipo_usuario='soldador'
                    )
                    
                    Soldador.objects.create(
                        usuario=usuario,
                        senha_simplificada=senha_simplificada
                    )
                    
                    messages.success(request, 'Soldador criado com sucesso')
                
                return redirect('core:gerenciar_soldadores')
                
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    # Listar soldadores
    soldadores = Soldador.objects.select_related('usuario').order_by('usuario__nome_completo')
    
    return render(request, 'admin/gerenciar_soldadores.html', {'soldadores': soldadores})

@login_required
def gerenciar_componentes(request):
    '''Gerenciar componentes'''
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:selecao_soldador')
    
    if request.method == 'POST':
        # Criar/editar componente
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        tempo_padrao = request.POST.get('tempo_padrao')
        considera_diametro = request.POST.get('considera_diametro') == 'on'
        formula_calculo = request.POST.get('formula_calculo', '')
        componente_id = request.POST.get('componente_id')
        
        try:
            if componente_id:
                # Editar
                componente = Componente.objects.get(id=componente_id)
                componente.nome = nome
                componente.descricao = descricao
                componente.tempo_padrao = tempo_padrao
                componente.considera_diametro = considera_diametro
                componente.formula_calculo = formula_calculo
                componente.save()
                
                messages.success(request, 'Componente atualizado com sucesso')
            else:
                # Criar
                Componente.objects.create(
                    nome=nome,
                    descricao=descricao,
                    tempo_padrao=tempo_padrao,
                    considera_diametro=considera_diametro,
                    formula_calculo=formula_calculo
                )
                
                messages.success(request, 'Componente criado com sucesso')
            
            return redirect('core:gerenciar_componentes')
            
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    # Listar componentes
    componentes = Componente.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'admin/gerenciar_componentes.html', {'componentes': componentes})

@login_required
def gerenciar_tipos_parada(request):
    '''Gerenciar tipos de parada'''
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:selecao_soldador')
    
    if request.method == 'POST':
        # Criar/editar tipo de parada
        nome = request.POST.get('nome')
        categoria = request.POST.get('categoria')
        penaliza_oee = request.POST.get('penaliza_oee') == 'on'
        requer_senha_especial = request.POST.get('requer_senha_especial') == 'on'
        cor_exibicao = request.POST.get('cor_exibicao', '#dc3545')
        tipo_id = request.POST.get('tipo_id')
        
        try:
            if tipo_id:
                # Editar
                tipo = TipoParada.objects.get(id=tipo_id)
                tipo.nome = nome
                tipo.categoria = categoria
                tipo.penaliza_oee = penaliza_oee
                tipo.requer_senha_especial = requer_senha_especial
                tipo.cor_exibicao = cor_exibicao
                tipo.save()
                
                messages.success(request, 'Tipo de parada atualizado com sucesso')
            else:
                # Criar
                TipoParada.objects.create(
                    nome=nome,
                    categoria=categoria,
                    penaliza_oee=penaliza_oee,
                    requer_senha_especial=requer_senha_especial,
                    cor_exibicao=cor_exibicao
                )
                
                messages.success(request, 'Tipo de parada criado com sucesso')
            
            return redirect('core:gerenciar_tipos_parada')
            
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    # Listar tipos de parada
    tipos_parada = TipoParada.objects.filter(ativo=True).order_by('categoria', 'nome')
    
    return render(request, 'admin/gerenciar_tipos_parada.html', {'tipos_parada': tipos_parada})

@login_required
def editar_apontamentos(request):
    '''Editar apontamentos existentes'''
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:selecao_soldador')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    soldador_id = request.GET.get('soldador_id')
    modulo_id = request.GET.get('modulo_id')
    
    # Query base
    apontamentos = Apontamento.objects.select_related(
        'soldador', 'modulo', 'componente', 'pedido'
    ).order_by('-inicio_processo')
    
    # Aplicar filtros
    if data_inicio:
        apontamentos = apontamentos.filter(inicio_processo__date__gte=data_inicio)
    
    if data_fim:
        apontamentos = apontamentos.filter(inicio_processo__date__lte=data_fim)
    
    if soldador_id:
        apontamentos = apontamentos.filter(soldador_id=soldador_id)
    
    if modulo_id:
        apontamentos = apontamentos.filter(modulo_id=modulo_id)
    
    # Paginação
    paginator = Paginator(apontamentos, 50)
    page = request.GET.get('page')
    apontamentos = paginator.get_page(page)
    
    # Dados para filtros
    soldadores = Soldador.objects.filter(ativo=True).order_by('usuario__nome_completo')
    modulos = Modulo.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'apontamentos': apontamentos,
        'soldadores': soldadores,
        'modulos': modulos,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'soldador_id': soldador_id,
            'modulo_id': modulo_id,
        }
    }
    
    return render(request, 'admin/editar_apontamentos.html', context)

@csrf_exempt
@login_required
def atualizar_apontamento(request):
    '''Atualizar dados de apontamento'''
    if request.method == 'POST' and request.user.tipo_usuario == 'admin':
        data = json.loads(request.body)
        apontamento_id = data.get('apontamento_id')
        
        try:
            with transaction.atomic():
                apontamento = Apontamento.objects.get(id=apontamento_id)
                
                # Dados antigos para auditoria
                dados_antes = {
                    'tempo_real': float(apontamento.tempo_real) if apontamento.tempo_real else None,
                    'tempo_padrao': float(apontamento.tempo_padrao),
                    'observacoes': apontamento.observacoes
                }
                
                # Atualizar dados
                if 'tempo_real' in data:
                    apontamento.tempo_real = data['tempo_real']
                
                if 'tempo_padrao' in data:
                    apontamento.tempo_padrao = data['tempo_padrao']
                
                if 'observacoes' in data:
                    apontamento.observacoes = data['observacoes']
                
                # Recalcular eficiência
                apontamento.calcular_eficiencia()
                apontamento.save()
                
                # Log de auditoria
                LogAuditoria.objects.create(
                    usuario=request.user,
                    acao='ATUALIZAR_APONTAMENTO',
                    tabela_afetada='Apontamento',
                    registro_id=str(apontamento.id),
                    dados_antes=dados_antes,
                    dados_depois={
                        'tempo_real': float(apontamento.tempo_real) if apontamento.tempo_real else None,
                        'tempo_padrao': float(apontamento.tempo_padrao),
                        'eficiencia': float(apontamento.eficiencia_calculada),
                        'observacoes': apontamento.observacoes
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'eficiencia': float(apontamento.eficiencia_calculada)
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
def logs_auditoria(request):
    '''Visualizar logs de auditoria'''
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:selecao_soldador')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    usuario_id = request.GET.get('usuario_id')
    acao = request.GET.get('acao')
    
    # Query base
    logs = LogAuditoria.objects.select_related('usuario').order_by('-timestamp')
    
    # Aplicar filtros
    if data_inicio:
        logs = logs.filter(timestamp__date__gte=data_inicio)
    
    if data_fim:
        logs = logs.filter(timestamp__date__lte=data_fim)
    
    if usuario_id:
        logs = logs.filter(usuario_id=usuario_id)
    
    if acao:
        logs = logs.filter(acao__icontains=acao)
    
    # Paginação
    paginator = Paginator(logs, 100)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    # Dados para filtros
    usuarios = Usuario.objects.filter(is_active=True).order_by('nome_completo')
    
    context = {
        'logs': logs,
        'usuarios': usuarios,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'usuario_id': usuario_id,
            'acao': acao,
        }
    }
    
    return render(request, 'admin/logs_auditoria.html', context)