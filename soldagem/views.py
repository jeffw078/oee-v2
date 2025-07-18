from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
import json
import uuid

from core.models import Usuario, Soldador, Modulo, Componente, LogAuditoria, SessaoOffline
from .models import Apontamento, Turno, Parada, TipoParada, Pedido

def selecao_soldador(request):
    '''Tela inicial - seleção de soldador (igual ao MVP)'''
    soldadores = Soldador.objects.filter(ativo=True).order_by('usuario__nome_completo')
    return render(request, 'soldagem/selecao_soldador.html', {'soldadores': soldadores})

@csrf_exempt
def login_soldador(request):
    '''Login simplificado do soldador'''
    if request.method == 'POST':
        data = json.loads(request.body)
        soldador_id = data.get('soldador_id')
        senha = data.get('senha')
        
        try:
            soldador = Soldador.objects.get(id=soldador_id, ativo=True)
            if soldador.senha_simplificada == senha:
                # Criar/atualizar sessão
                request.session['soldador_id'] = soldador.id
                request.session['soldador_nome'] = soldador.usuario.nome_completo
                
                # Criar turno se não existir
                turno, created = Turno.objects.get_or_create(
                    soldador=soldador,
                    data_turno=timezone.now().date(),
                    defaults={
                        'inicio_turno': timezone.now(),
                        'horas_disponiveis': 8,
                        'status': 'ativo'
                    }
                )
                
                # Log de auditoria
                LogAuditoria.objects.create(
                    usuario=soldador.usuario,
                    acao='LOGIN_SOLDADOR',
                    tabela_afetada='Turno',
                    registro_id=str(turno.id),
                    dados_depois={'soldador': soldador.usuario.nome_completo}
                )
                
                # Configurar dispositivo offline
                dispositivo_id = request.session.get('dispositivo_id', str(uuid.uuid4()))
                request.session['dispositivo_id'] = dispositivo_id
                
                SessaoOffline.objects.update_or_create(
                    dispositivo_id=dispositivo_id,
                    defaults={
                        'soldador': soldador,
                        'ultimo_sync': timezone.now(),
                        'status_conexao': True
                    }
                )
                
                return JsonResponse({'success': True, 'redirect': '/apontamento/'})
            else:
                return JsonResponse({'success': False, 'message': 'Senha incorreta'})
        except Soldador.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Soldador não encontrado'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

def apontamento(request):
    '''Tela principal de apontamento (igual ao MVP)'''
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
    
    # Dados para saudação
    now = timezone.now()
    if now.hour < 12:
        saudacao = "Bom dia"
    elif now.hour < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"
    
    context = {
        'soldador': soldador,
        'modulos': modulos,
        'saudacao': saudacao,
        'apontamento_atual': apontamento_atual,
        'now': now
    }
    
    return render(request, 'soldagem/apontamento.html', context)

@csrf_exempt
def iniciar_modulo(request):
    '''Inicia processo de seleção de componente do módulo'''
    if request.method == 'POST':
        data = json.loads(request.body)
        modulo_id = data.get('modulo_id')
        pedido_numero = data.get('pedido')
        poste_numero = data.get('poste')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'})
        
        try:
            soldador = Soldador.objects.get(id=soldador_id)
            modulo = Modulo.objects.get(id=modulo_id)
            
            # Criar/buscar pedido
            pedido, created = Pedido.objects.get_or_create(
                numero=pedido_numero,
                defaults={'descricao': f'Pedido {pedido_numero}'}
            )
            
            # Armazenar dados na sessão
            request.session['modulo_atual'] = modulo_id
            request.session['pedido_atual'] = pedido.id
            request.session['poste_atual'] = poste_numero
            
            # Buscar componentes disponíveis
            componentes = Componente.objects.filter(ativo=True).order_by('nome')
            
            componentes_data = []
            for comp in componentes:
                componentes_data.append({
                    'id': comp.id,
                    'nome': comp.nome,
                    'tempo_padrao': float(comp.tempo_padrao),
                    'considera_diametro': comp.considera_diametro,
                    'formula_calculo': comp.formula_calculo
                })
            
            return JsonResponse({
                'success': True,
                'componentes': componentes_data,
                'modulo_nome': modulo.nome
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@csrf_exempt
def iniciar_componente(request):
    '''Inicia processo de soldagem de componente'''
    if request.method == 'POST':
        data = json.loads(request.body)
        componente_id = data.get('componente_id')
        diametro = data.get('diametro')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'})
        
        try:
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
                        # Usar fórmula personalizada se disponível
                        if componente.formula_calculo:
                            tempo_padrao = eval(componente.formula_calculo.replace('diametro', str(diametro)))
                        else:
                            tempo_padrao = float(diametro) * 0.05  # Padrão
                    except:
                        pass
                
                # Criar apontamento
                apontamento = Apontamento.objects.create(
                    soldador=soldador,
                    modulo=modulo,
                    componente=componente,
                    pedido=pedido,
                    numero_poste_tubo=request.session.get('poste_atual'),
                    diametro=diametro if componente.considera_diametro else None,
                    inicio_processo=timezone.now(),
                    tempo_padrao=tempo_padrao
                )
                
                # Log de auditoria
                LogAuditoria.objects.create(
                    usuario=soldador.usuario,
                    acao='INICIAR_COMPONENTE',
                    tabela_afetada='Apontamento',
                    registro_id=str(apontamento.id),
                    dados_depois={
                        'componente': componente.nome,
                        'pedido': pedido.numero,
                        'poste': request.session.get('poste_atual')
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'apontamento_id': apontamento.id,
                    'componente_nome': componente.nome,
                    'tempo_padrao': float(tempo_padrao)
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@csrf_exempt
def finalizar_componente(request):
    '''Finaliza processo de soldagem'''
    if request.method == 'POST':
        data = json.loads(request.body)
        apontamento_id = data.get('apontamento_id')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'})
        
        try:
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
                
                # Log de auditoria
                LogAuditoria.objects.create(
                    usuario=apontamento.soldador.usuario,
                    acao='FINALIZAR_COMPONENTE',
                    tabela_afetada='Apontamento',
                    registro_id=str(apontamento.id),
                    dados_depois={
                        'tempo_real': float(apontamento.tempo_real),
                        'eficiencia': float(apontamento.eficiencia_calculada)
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'tempo_real': float(apontamento.tempo_real),
                    'eficiencia': float(apontamento.eficiencia_calculada)
                })
                
        except Apontamento.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Apontamento não encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

def finalizar_turno(request):
    '''Finaliza turno do soldador'''
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    try:
        soldador = Soldador.objects.get(id=soldador_id)
        
        # Finalizar turno atual
        turno = Turno.objects.filter(
            soldador=soldador,
            data_turno=timezone.now().date(),
            status='ativo'
        ).first()
        
        if turno:
            turno.fim_turno = timezone.now()
            turno.status = 'finalizado'
            turno.save()
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario=soldador.usuario,
                acao='FINALIZAR_TURNO',
                tabela_afetada='Turno',
                registro_id=str(turno.id),
                dados_depois={'fim_turno': turno.fim_turno.isoformat()}
            )
        
        # Limpar sessão
        request.session.flush()
        
        return redirect('soldagem:selecao_soldador')
        
    except Exception as e:
        messages.error(request, f'Erro ao finalizar turno: {str(e)}')
        return redirect('soldagem:apontamento')

# Status de conexão para funcionalidade offline
@csrf_exempt
def status_conexao(request):
    '''Verifica status de conexão'''
    dispositivo_id = request.session.get('dispositivo_id')
    if dispositivo_id:
        try:
            sessao = SessaoOffline.objects.get(dispositivo_id=dispositivo_id)
            sessao.status_conexao = True
            sessao.ultimo_sync = timezone.now()
            sessao.save()
            
            return JsonResponse({
                'success': True,
                'conectado': True,
                'ultimo_sync': sessao.ultimo_sync.isoformat()
            })
        except SessaoOffline.DoesNotExist:
            pass
    
    return JsonResponse({'success': True, 'conectado': False})

@csrf_exempt
def sincronizar_dados(request):
    '''Sincroniza dados offline'''
    if request.method == 'POST':
        data = json.loads(request.body)
        dispositivo_id = request.session.get('dispositivo_id')
        
        if not dispositivo_id:
            return JsonResponse({'success': False, 'message': 'Dispositivo não identificado'})
        
        try:
            sessao = SessaoOffline.objects.get(dispositivo_id=dispositivo_id)
            
            # Processar dados offline
            dados_offline = data.get('dados_offline', [])
            
            for dado in dados_offline:
                # Aqui você processaria cada tipo de dado offline
                # Por exemplo: apontamentos, paradas, etc.
                pass
            
            # Atualizar cache da sessão
            sessao.dados_cache = data.get('cache', {})
            sessao.ultimo_sync = timezone.now()
            sessao.save()
            
            return JsonResponse({
                'success': True,
                'sincronizado': len(dados_offline),
                'timestamp': timezone.now().isoformat()
            })
            
        except SessaoOffline.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Sessão não encontrada'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})