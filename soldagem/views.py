from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
import json
import pytz

from core.models import Soldador, Usuario, LogAuditoria
try:
    from core.models import Modulo, Componente
except ImportError:
    from .models import Modulo, Componente

from .models import Pedido, Apontamento, TipoParada, Parada, Turno
from qualidade.models import TipoDefeito, Defeito

def selecao_soldador(request):
    """Tela de seleção de soldador"""
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
        
        soldador = get_object_or_404(Soldador, id=soldador_id, ativo=True)
        
        if soldador.senha_simplificada == senha:
            # Criar ou atualizar turno
            hoje = timezone.now().date()
            turno, created = Turno.objects.get_or_create(
                soldador=soldador,
                data_turno=hoje,
                defaults={
                    'inicio_turno': timezone.now(),
                    'horas_disponiveis': 8,
                    'status': 'ativo'
                }
            )
            
            if not created and turno.status == 'finalizado':
                turno.status = 'ativo'
                turno.save()
            
            # Salvar na sessão
            request.session['soldador_id'] = soldador.id
            request.session['turno_id'] = turno.id
            request.session.save()
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario=soldador.usuario,
                acao='LOGIN_SOLDADOR',
                tabela_afetada='Soldador',
                registro_id=soldador.id,
                dados_depois={'soldador': soldador.usuario.nome_completo}
            )
            
            return JsonResponse({
                'success': True,
                'redirect': '/apontamento/',
                'soldador_nome': soldador.usuario.nome_completo
            })
        else:
            return JsonResponse({'success': False, 'message': 'Senha incorreta'}, status=401)
            
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
    
    # Importar Modulo do local correto
    try:
        from core.models import Modulo
        modulos = Modulo.objects.filter(ativo=True).order_by('ordem_exibicao')
    except ImportError:
        # Fallback se Modulo estiver em soldagem.models
        modulos = Modulo.objects.filter(ativo=True).order_by('ordem_exibicao')
    
    # Verificar se há apontamento em andamento
    apontamento_atual = Apontamento.objects.filter(
        soldador=soldador,
        fim_processo__isnull=True
    ).first()
    
    # Verificar se há parada em andamento
    parada_atual = Parada.objects.filter(
        soldador=soldador,
        fim__isnull=True
    ).first()
    
    # Saudação baseada no horário brasileiro
    tz_sp = pytz.timezone('America/Sao_Paulo')
    now_sp = timezone.now().astimezone(tz_sp)
    
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
        'parada_atual': parada_atual,
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
        
    except json.JSONDecodeError:
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
            
    except (Soldador.DoesNotExist, Componente.DoesNotExist, Modulo.DoesNotExist, Pedido.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'Dados não encontrados'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def finalizar_componente(request):
    """Finaliza processo de soldagem - CORRIGIDO ERRO 500"""
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
            
            # CORREÇÃO: Calcular tempo real e eficiência
            if apontamento.fim_processo and apontamento.inicio_processo:
                diff = apontamento.fim_processo - apontamento.inicio_processo
                apontamento.tempo_real = diff.total_seconds() / 60
                
                # Calcular eficiência
                if apontamento.tempo_real and apontamento.tempo_padrao and apontamento.tempo_real > 0:
                    apontamento.eficiencia_calculada = (float(apontamento.tempo_padrao) / float(apontamento.tempo_real)) * 100
                else:
                    apontamento.eficiencia_calculada = 0
                    
            apontamento.save()
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario_id=soldador_id,
                acao='FINALIZAR_COMPONENTE',
                tabela_afetada='Apontamento',
                registro_id=apontamento.id,
                dados_depois={
                    'componente': apontamento.componente.nome,
                    'tempo_real': float(apontamento.tempo_real or 0),
                    'eficiencia': float(apontamento.eficiencia_calculada or 0)
                }
            )
            
            return JsonResponse({
                'success': True,
                'tempo_real': float(apontamento.tempo_real or 0),
                'eficiencia': float(apontamento.eficiencia_calculada or 0)
            })
            
    except Apontamento.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Apontamento não encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# ==================== FUNCIONALIDADES DE PARADAS ====================

@csrf_exempt
def iniciar_parada(request):
    """Inicia uma parada (geral, qualidade ou manutenção)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        tipo_parada_id = data.get('tipo_parada_id')
        motivo_detalhado = data.get('motivo_detalhado', '')
        senha_especial = data.get('senha_especial')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        with transaction.atomic():
            soldador = Soldador.objects.get(id=soldador_id)
            tipo_parada = TipoParada.objects.get(id=tipo_parada_id, ativo=True)
            
            # Verificar se requer senha especial
            if tipo_parada.requer_senha_especial:
                usuario_autorizacao = None
                if tipo_parada.categoria == 'qualidade':
                    try:
                        from django.contrib.auth import authenticate
                        usuario_autorizacao = authenticate(username='qualidade', password=senha_especial)
                        if not usuario_autorizacao or usuario_autorizacao.tipo_usuario != 'qualidade':
                            return JsonResponse({'success': False, 'message': 'Senha de qualidade inválida'})
                    except:
                        return JsonResponse({'success': False, 'message': 'Senha de qualidade inválida'})
                        
                elif tipo_parada.categoria == 'manutencao':
                    try:
                        from django.contrib.auth import authenticate
                        usuario_autorizacao = authenticate(username='manutencao', password=senha_especial)
                        if not usuario_autorizacao or usuario_autorizacao.tipo_usuario != 'manutencao':
                            return JsonResponse({'success': False, 'message': 'Senha de manutenção inválida'})
                    except:
                        return JsonResponse({'success': False, 'message': 'Senha de manutenção inválida'})
            
            # Verificar se já existe parada em andamento
            parada_existente = Parada.objects.filter(
                soldador=soldador,
                fim__isnull=True
            ).first()
            
            if parada_existente:
                return JsonResponse({
                    'success': False, 
                    'message': 'Finalize a parada atual primeiro'
                })
            
            # Buscar apontamento em andamento (se houver)
            apontamento_atual = Apontamento.objects.filter(
                soldador=soldador,
                fim_processo__isnull=True
            ).first()
            
            # Criar parada
            parada = Parada.objects.create(
                tipo_parada=tipo_parada,
                soldador=soldador,
                apontamento=apontamento_atual,
                inicio=timezone.now(),
                motivo_detalhado=motivo_detalhado,
                usuario_autorizacao=usuario_autorizacao
            )
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario=usuario_autorizacao or soldador.usuario,
                acao='INICIAR_PARADA',
                tabela_afetada='Parada',
                registro_id=parada.id,
                dados_depois={
                    'tipo_parada': tipo_parada.nome,
                    'categoria': tipo_parada.categoria,
                    'soldador': soldador.usuario.nome_completo
                }
            )
            
            return JsonResponse({
                'success': True,
                'parada_id': parada.id,
                'tipo_parada': tipo_parada.nome,
                'categoria': tipo_parada.categoria
            })
            
    except (Soldador.DoesNotExist, TipoParada.DoesNotExist):
        return JsonResponse({'success': False, 'message': 'Dados não encontrados'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def finalizar_parada(request):
    """Finaliza uma parada em andamento"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        parada_id = data.get('parada_id')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        with transaction.atomic():
            parada = Parada.objects.get(
                id=parada_id,
                soldador_id=soldador_id,
                fim__isnull=True
            )
            
            # Finalizar parada
            parada.fim = timezone.now()
            
            # Calcular duração em minutos
            if parada.fim and parada.inicio:
                diff = parada.fim - parada.inicio
                parada.duracao_minutos = diff.total_seconds() / 60
                
            parada.save()
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario_id=soldador_id,
                acao='FINALIZAR_PARADA',
                tabela_afetada='Parada',
                registro_id=parada.id,
                dados_depois={
                    'tipo_parada': parada.tipo_parada.nome,
                    'duracao_minutos': float(parada.duracao_minutos or 0)
                }
            )
            
            return JsonResponse({
                'success': True,
                'duracao_minutos': float(parada.duracao_minutos or 0),
                'tipo_parada': parada.tipo_parada.nome
            })
            
    except Parada.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Parada não encontrada'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def buscar_tipos_parada(request):
    """Busca tipos de parada por categoria"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        categoria = request.GET.get('categoria', 'geral')
        
        tipos_parada = TipoParada.objects.filter(
            categoria=categoria,
            ativo=True
        ).order_by('nome')
        
        tipos_data = []
        for tipo in tipos_parada:
            tipos_data.append({
                'id': tipo.id,
                'nome': tipo.nome,
                'categoria': tipo.categoria,
                'penaliza_oee': tipo.penaliza_oee,
                'requer_senha_especial': tipo.requer_senha_especial,
                'cor_exibicao': tipo.cor_exibicao
            })
        
        return JsonResponse({
            'success': True,
            'tipos_parada': tipos_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# ==================== PAINÉIS ESPECÍFICOS ====================

def painel_qualidade(request):
    """Painel de qualidade"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    
    # Buscar tipos de defeito ativos
    tipos_defeito = TipoDefeito.objects.filter(ativo=True).order_by('nome')
    
    # Buscar apontamentos do dia atual para seleção
    hoje = timezone.now().date()
    apontamentos_hoje = Apontamento.objects.filter(
        soldador=soldador,
        inicio_processo__date=hoje,
        fim_processo__isnull=False
    ).select_related('componente').order_by('-inicio_processo')
    
    context = {
        'soldador': soldador,
        'tipos_defeito': tipos_defeito,
        'apontamentos_hoje': apontamentos_hoje,
    }
    
    return render(request, 'soldagem/painel_qualidade.html', context)

def painel_paradas(request):
    """Painel de paradas gerais"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    
    # Buscar tipos de parada gerais
    tipos_parada = TipoParada.objects.filter(
        categoria='geral',
        ativo=True
    ).order_by('nome')
    
    context = {
        'soldador': soldador,
        'tipos_parada': tipos_parada,
    }
    
    return render(request, 'soldagem/painel_paradas.html', context)

def painel_manutencao(request):
    """Painel de manutenção"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    
    # Buscar tipos de parada de manutenção
    tipos_parada = TipoParada.objects.filter(
        categoria='manutencao',
        ativo=True
    ).order_by('nome')
    
    context = {
        'soldador': soldador,
        'tipos_parada': tipos_parada,
    }
    
    return render(request, 'soldagem/painel_manutencao.html', context)

def finalizar_turno(request):
    """Finaliza turno do soldador"""
    soldador_id = request.session.get('soldador_id')
    turno_id = request.session.get('turno_id')
    
    if turno_id:
        try:
            turno = Turno.objects.get(id=turno_id)
            turno.fim_turno = timezone.now()
            turno.status = 'finalizado'
            turno.save()
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario_id=soldador_id,
                acao='FINALIZAR_TURNO',
                tabela_afetada='Turno',
                registro_id=turno.id,
                dados_depois={'fim_turno': turno.fim_turno.isoformat()}
            )
            
        except Turno.DoesNotExist:
            pass
    
    # Limpar sessão
    request.session.flush()
    return redirect('soldagem:selecao_soldador')