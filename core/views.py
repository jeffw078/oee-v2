from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.core.paginator import Paginator
import json
from soldagem.models import (
    Usuario, Soldador, Modulo, Componente, Apontamento, 
    TipoParada, Parada, Turno
)
from qualidade.models import TipoDefeito, Defeito

@login_required
def dashboard_admin(request):
    """Dashboard administrativo principal"""
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado ao painel administrativo')
        return redirect('soldagem:apontamento')
    
    # Estatísticas gerais
    hoje = timezone.now().date()
    
    stats = {
        'total_soldadores': Soldador.objects.filter(ativo=True).count(),
        'total_componentes': Componente.objects.filter(ativo=True).count(),
        'total_modulos': Modulo.objects.filter(ativo=True).count(),
        'apontamentos_hoje': Apontamento.objects.filter(inicio_processo__date=hoje).count(),
        'defeitos_hoje': Defeito.objects.filter(data_deteccao__date=hoje).count(),
        'paradas_hoje': Parada.objects.filter(inicio__date=hoje).count(),
        'soldadores_ativos': Turno.objects.filter(data_turno=hoje, status='ativo').count()
    }
    
    # Últimas atividades
    ultimos_apontamentos = Apontamento.objects.filter(
        inicio_processo__date=hoje
    ).select_related('soldador__usuario', 'componente', 'modulo').order_by('-inicio_processo')[:10]
    
    context = {
        'stats': stats,
        'ultimos_apontamentos': ultimos_apontamentos,
        'data_atual': hoje,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def gerenciar_soldadores(request):
    """Gerenciamento de soldadores"""
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    if request.method == 'POST':
        # Criar/editar soldador
        soldador_id = request.POST.get('soldador_id')
        nome_completo = request.POST.get('nome_completo')
        username = request.POST.get('username')
        senha_simplificada = request.POST.get('senha_simplificada')
        email = request.POST.get('email', '')
        
        try:
            if soldador_id:  # Editar
                soldador = Soldador.objects.get(id=soldador_id)
                soldador.usuario.nome_completo = nome_completo
                soldador.usuario.username = username
                soldador.usuario.email = email
                soldador.usuario.save()
                soldador.senha_simplificada = senha_simplificada
                soldador.save()
                messages.success(request, 'Soldador atualizado com sucesso!')
            else:  # Criar
                # Verificar se username já existe
                if Usuario.objects.filter(username=username).exists():
                    messages.error(request, 'Nome de usuário já existe')
                else:
                    usuario = Usuario.objects.create_user(
                        username=username,
                        password='soldador123',  # Senha padrão
                        nome_completo=nome_completo,
                        email=email,
                        tipo_usuario='soldador'
                    )
                    Soldador.objects.create(
                        usuario=usuario,
                        senha_simplificada=senha_simplificada
                    )
                    messages.success(request, 'Soldador criado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    soldadores = Soldador.objects.select_related('usuario').filter(ativo=True).order_by('usuario__nome_completo')
    
    context = {
        'soldadores': soldadores,
    }
    
    return render(request, 'admin/gerenciar_soldadores.html', context)

@login_required
def gerenciar_componentes(request):
    """Gerenciamento de componentes"""
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    if request.method == 'POST':
        # Criar/editar componente
        componente_id = request.POST.get('componente_id')
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        tempo_padrao = request.POST.get('tempo_padrao')
        considera_diametro = request.POST.get('considera_diametro') == 'on'
        formula_calculo = request.POST.get('formula_calculo', '')
        
        try:
            if componente_id:  # Editar
                componente = Componente.objects.get(id=componente_id)
                componente.nome = nome
                componente.descricao = descricao
                componente.tempo_padrao = tempo_padrao
                componente.considera_diametro = considera_diametro
                componente.formula_calculo = formula_calculo
                componente.save()
                messages.success(request, 'Componente atualizado com sucesso!')
            else:  # Criar
                Componente.objects.create(
                    nome=nome,
                    descricao=descricao,
                    tempo_padrao=tempo_padrao,
                    considera_diametro=considera_diametro,
                    formula_calculo=formula_calculo
                )
                messages.success(request, 'Componente criado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    componentes = Componente.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'componentes': componentes,
    }
    
    return render(request, 'admin/gerenciar_componentes.html', context)

@login_required
def gerenciar_paradas(request):
    """Gerenciamento de tipos de parada"""
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    if request.method == 'POST':
        # Criar/editar tipo de parada
        tipo_id = request.POST.get('tipo_id')
        nome = request.POST.get('nome')
        categoria = request.POST.get('categoria')
        penaliza_oee = request.POST.get('penaliza_oee') == 'on'
        requer_senha_especial = request.POST.get('requer_senha_especial') == 'on'
        cor_exibicao = request.POST.get('cor_exibicao', '#6c757d')
        
        try:
            if tipo_id:  # Editar
                tipo = TipoParada.objects.get(id=tipo_id)
                tipo.nome = nome
                tipo.categoria = categoria
                tipo.penaliza_oee = penaliza_oee
                tipo.requer_senha_especial = requer_senha_especial
                tipo.cor_exibicao = cor_exibicao
                tipo.save()
                messages.success(request, 'Tipo de parada atualizado com sucesso!')
            else:  # Criar
                TipoParada.objects.create(
                    nome=nome,
                    categoria=categoria,
                    penaliza_oee=penaliza_oee,
                    requer_senha_especial=requer_senha_especial,
                    cor_exibicao=cor_exibicao
                )
                messages.success(request, 'Tipo de parada criado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    tipos_parada = TipoParada.objects.filter(ativo=True).order_by('categoria', 'nome')
    
    context = {
        'tipos_parada': tipos_parada,
        'categorias': TipoParada.CATEGORIA_CHOICES,
    }
    
    return render(request, 'admin/gerenciar_paradas.html', context)

@login_required
def editar_apontamentos(request):
    """Edição de apontamentos"""
    if request.user.tipo_usuario != 'admin':
        messages.error(request, 'Acesso negado')
        return redirect('soldagem:apontamento')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', timezone.now().date())
    data_fim = request.GET.get('data_fim', timezone.now().date())
    soldador_id = request.GET.get('soldador_id')
    modulo_id = request.GET.get('modulo_id')
    
    # Buscar apontamentos
    apontamentos = Apontamento.objects.filter(
        inicio_processo__date__gte=data_inicio,
        inicio_processo__date__lte=data_fim
    ).select_related('soldador__usuario', 'componente', 'modulo', 'pedido')
    
    if soldador_id:
        apontamentos = apontamentos.filter(soldador_id=soldador_id)
    if modulo_id:
        apontamentos = apontamentos.filter(modulo_id=modulo_id)
    
    apontamentos = apontamentos.order_by('-inicio_processo')
    
    # Paginação
    paginator = Paginator(apontamentos, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'soldadores': Soldador.objects.filter(ativo=True),
        'modulos': Modulo.objects.filter(ativo=True),
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'soldador_selecionado': soldador_id,
        'modulo_selecionado': modulo_id,
    }
    
    return render(request, 'admin/editar_apontamentos.html', context)

@csrf_exempt
@login_required
def api_excluir_registro(request):
    """API para excluir registros diversos"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'message': 'Método não permitido'})
    
    if request.user.tipo_usuario != 'admin':
        return JsonResponse({'success': False, 'message': 'Acesso negado'})
    
    try:
        dados = json.loads(request.body)
        tipo = dados.get('tipo')
        registro_id = dados.get('id')
        
        if tipo == 'soldador':
            soldador = Soldador.objects.get(id=registro_id)
            soldador.ativo = False
            soldador.save()
            return JsonResponse({'success': True, 'message': 'Soldador desativado'})
        
        elif tipo == 'componente':
            componente = Componente.objects.get(id=registro_id)
            componente.ativo = False
            componente.save()
            return JsonResponse({'success': True, 'message': 'Componente desativado'})
        
        elif tipo == 'tipo_parada':
            tipo_parada = TipoParada.objects.get(id=registro_id)
            tipo_parada.ativo = False
            tipo_parada.save()
            return JsonResponse({'success': True, 'message': 'Tipo de parada desativado'})
        
        else:
            return JsonResponse({'success': False, 'message': 'Tipo de registro inválido'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro: {str(e)}'})