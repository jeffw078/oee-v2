from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from core.models import Soldador, Modulo, Componente
from .models import Apontamento, Turno, Pedido

def selecao_soldador(request):
    """Tela inicial - seleção de soldador"""
    soldadores = Soldador.objects.filter(ativo=True).order_by('usuario__nome_completo')
    return render(request, 'soldagem/selecao_soldador.html', {'soldadores': soldadores})

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
            return JsonResponse({'success': False, 'message': 'ID e senha obrigatórios'}, status=400)
        
        soldador = Soldador.objects.get(id=soldador_id, ativo=True)
        
        if soldador.senha_simplificada == senha:
            request.session['soldador_id'] = soldador.id
            request.session['soldador_nome'] = soldador.usuario.nome_completo
            request.session.save()
            
            # Criar turno
            Turno.objects.get_or_create(
                soldador=soldador,
                data_turno=timezone.now().date(),
                defaults={'inicio_turno': timezone.now(), 'status': 'ativo'}
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Login realizado com sucesso',
                'soldador': soldador.usuario.nome_completo,
                'redirect': '/apontamento/'
            })
        else:
            return JsonResponse({'success': False, 'message': 'Senha incorreta'}, status=401)
        
    except Soldador.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Soldador não encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro interno: {str(e)}'}, status=500)

def apontamento(request):
    """Tela principal de apontamento"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    modulos = Modulo.objects.filter(ativo=True).order_by('ordem_exibicao')
    
    # Verificar se há apontamento em andamento
    apontamento_atual = Apontamento.objects.filter(
        soldador=soldador,
        fim_processo__isnull=True
    ).first()
    
    # CORREÇÃO DA SAUDAÇÃO - usar horário local brasileiro
    from datetime import datetime
    import pytz
    
    # Usar timezone de São Paulo
    tz_sp = pytz.timezone('America/Sao_Paulo')
    now_sp = datetime.now(tz_sp)
    
    if now_sp.hour < 12:
        saudacao = "Bom dia"
    elif now_sp.hour < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"
    
    context = {
        'soldador': soldador,
        'modulos': modulos,
        'saudacao': saudacao,
        'apontamento_atual': apontamento_atual,
        'now': now_sp
    }
    
    return render(request, 'soldagem/apontamento.html', context)

@csrf_exempt
def iniciar_modulo(request):
    """Inicia processo de seleção de componente do módulo"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        modulo_id = data.get('modulo_id')
        pedido_numero = data.get('pedido')
        poste_numero = data.get('poste')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        # Buscar módulo
        try:
            modulo = Modulo.objects.get(id=modulo_id)
        except Modulo.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Módulo não encontrado'}, status=404)
        
        # Criar/buscar pedido
        pedido, created = Pedido.objects.get_or_create(
            numero=pedido_numero,
            defaults={'descricao': f'Pedido {pedido_numero}'}
        )
        
        # Armazenar dados na sessão
        request.session['modulo_atual'] = modulo_id
        request.session['pedido_atual'] = pedido.id
        request.session['poste_atual'] = poste_numero
        request.session.save()
        
        # Buscar componentes disponíveis
        componentes = Componente.objects.filter(ativo=True).order_by('nome')
        
        componentes_data = []
        for comp in componentes:
            componentes_data.append({
                'id': comp.id,
                'nome': comp.nome,
                'tempo_padrao': float(comp.tempo_padrao),
                'considera_diametro': comp.considera_diametro,
                'formula_calculo': comp.formula_calculo or ''
            })
        
        return JsonResponse({
            'success': True,
            'componentes': componentes_data,
            'modulo_nome': modulo.nome
        })
        
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def iniciar_componente(request):
    """Inicia processo de soldagem de componente"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        componente_id = data.get('componente_id')
        diametro = data.get('diametro')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        with transaction.atomic():
            soldador = Soldador.objects.get(id=soldador_id)
            componente = Componente.objects.get(id=componente_id)
            modulo = Modulo.objects.get(id=request.session.get('modulo_atual'))
            pedido = Pedido.objects.get(id=request.session.get('pedido_atual'))
            
            # Verificar se já existe apontamento em andamento
            apontamento_existente = Apontamento.objects.filter(
                soldador=soldador,
                fim_processo__isnull=True
            ).first()
            
            if apontamento_existente:
                return JsonResponse({
                    'success': False, 
                    'message': 'Finalize o apontamento atual primeiro'
                })
            
            # Calcular tempo padrão
            tempo_padrao = componente.tempo_padrao
            if componente.considera_diametro and diametro:
                try:
                    if componente.formula_calculo:
                        tempo_padrao = eval(componente.formula_calculo.replace('diametro', str(diametro)))
                    else:
                        tempo_padrao = float(diametro) * 0.05
                except:
                    pass
            
            # Criar apontamento
            apontamento = Apontamento.objects.create(
                soldador=soldador,
                modulo=modulo,
                componente=componente,
                pedido=pedido,
                numero_poste_tubo=request.session.get('poste_atual', ''),
                diametro=diametro if componente.considera_diametro else None,
                inicio_processo=timezone.now(),
                tempo_padrao=tempo_padrao
            )
            
            return JsonResponse({
                'success': True,
                'apontamento_id': apontamento.id,
                'componente_nome': componente.nome,
                'tempo_padrao': float(tempo_padrao)
            })
            
    except (Soldador.DoesNotExist, Componente.DoesNotExist, Modulo.DoesNotExist, Pedido.DoesNotExist) as e:
        return JsonResponse({'success': False, 'message': 'Dados não encontrados'}, status=404)
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def finalizar_componente(request):
    """Finaliza processo de soldagem"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        apontamento_id = data.get('apontamento_id')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        with transaction.atomic():
            apontamento = Apontamento.objects.get(
                id=apontamento_id,
                soldador_id=soldador_id,
                fim_processo__isnull=True
            )
            
            # Finalizar apontamento
            apontamento.fim_processo = timezone.now()
            apontamento.calcular_tempo_real()
            apontamento.calcular_eficiencia()
            apontamento.save()
            
            return JsonResponse({
                'success': True,
                'tempo_real': float(apontamento.tempo_real or 0),
                'eficiencia': float(apontamento.eficiencia_calculada or 0)
            })
            
    except Apontamento.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Apontamento não encontrado'}, status=404)
    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def painel_qualidade(request):
    """Painel de qualidade"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    return render(request, 'soldagem/painel_qualidade.html', {'soldador': soldador})

def painel_paradas(request):
    """Painel de paradas"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    return render(request, 'soldagem/painel_paradas.html', {'soldador': soldador})

def painel_manutencao(request):
    """Painel de manutenção"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    return render(request, 'soldagem/painel_manutencao.html', {'soldador': soldador})

def finalizar_turno(request):
    """Finaliza turno do soldador"""
    request.session.flush()
    return redirect('soldagem:selecao_soldador')
