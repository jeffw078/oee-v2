from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import json
from datetime import timedelta, datetime

# IMPORTAR TODOS OS MODELOS DO MESMO APP
from .models import (
    Usuario, Soldador, Modulo, Componente, Pedido, 
    Turno, Apontamento, TipoParada, Parada, LogAuditoria
)
# ==================== VIEWS PRINCIPAIS ====================

def selecao_soldador(request):
    """Tela inicial de seleção de soldador"""
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
            return JsonResponse({'success': False, 'message': 'Soldador e senha são obrigatórios'}, status=400)
        
        soldador = get_object_or_404(Soldador, id=soldador_id, ativo=True)
        
        if soldador.senha_simplificada != senha:
            return JsonResponse({'success': False, 'message': 'Senha incorreta'}, status=401)
        
        # Criar ou buscar turno ativo
        hoje = timezone.now().date()
        turno, created = Turno.objects.get_or_create(
            soldador=soldador,
            data_turno=hoje,
            status='ativo',
            defaults={
                'inicio_turno': timezone.now(),
                'horas_disponiveis': 8.0
            }
        )
        
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
            dados_depois={'turno_criado': created}
        )
        
        return JsonResponse({
            'success': True,
            'soldador_nome': soldador.usuario.nome_completo,
            'turno_id': turno.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def apontamento(request):
    """Tela principal de apontamento"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    soldador = get_object_or_404(Soldador, id=soldador_id)
    modulos = Modulo.objects.filter(ativo=True).order_by('ordem_exibicao')
    
    # Verificar se há apontamento em andamento
    apontamento_ativo = Apontamento.objects.filter(
        soldador=soldador,
        fim_processo__isnull=True
    ).first()
    
    # Verificar se há parada em andamento
    parada_ativa = Parada.objects.filter(
        soldador=soldador,
        fim__isnull=True
    ).first()
    
    context = {
        'soldador': soldador,
        'modulos': modulos,
        'apontamento_ativo': apontamento_ativo,
        'parada_ativa': parada_ativa,
        'agora': timezone.now(),
    }
    
    return render(request, 'soldagem/apontamento.html', context)

def finalizar_turno(request):
    """Finaliza turno do soldador"""
    soldador_id = request.session.get('soldador_id')
    turno_id = request.session.get('turno_id')
    
    if soldador_id and turno_id:
        try:
            # Finalizar apontamentos em aberto
            Apontamento.objects.filter(
                soldador_id=soldador_id,
                fim_processo__isnull=True
            ).update(fim_processo=timezone.now())
            
            # Finalizar paradas em aberto
            Parada.objects.filter(
                soldador_id=soldador_id,
                fim__isnull=True
            ).update(fim=timezone.now())
            
            # Finalizar turno
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
                dados_depois={
                    'fim_turno': turno.fim_turno.isoformat(),
                    'duracao_horas': float((turno.fim_turno - turno.inicio_turno).total_seconds() / 3600)
                }
            )
            
        except Exception as e:
            messages.error(request, f'Erro ao finalizar turno: {str(e)}')
    
    # Limpar sessão
    request.session.flush()
    return redirect('soldagem:selecao_soldador')

# ==================== APIS DE APONTAMENTO ====================

@csrf_exempt
def iniciar_modulo(request):
    """Inicia seleção de módulo e captura dados do pedido"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        modulo_id = data.get('modulo_id')
        pedido_numero = data.get('pedido_numero')
        poste_numero = data.get('poste_numero')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        # Buscar módulo
        try:
            modulo = Modulo.objects.get(id=modulo_id, ativo=True)
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
            componente = Componente.objects.get(id=componente_id, ativo=True)
            modulo = Modulo.objects.get(id=request.session.get('modulo_atual'))
            pedido = Pedido.objects.get(id=request.session.get('pedido_atual'))
            
            # Verificar se já existe apontamento em andamento
            apontamento_existente = Apontamento.objects.filter(
                soldador=soldador,
                fim_processo__isnull=True
            ).first()
            
            if apontamento_existente:
                return JsonResponse({'success': False, 'message': 'Já existe um apontamento em andamento'}, status=400)
            
            # Calcular tempo padrão
            tempo_padrao = componente.tempo_padrao
            if componente.considera_diametro and diametro:
                # Aplicar fórmula baseada no diâmetro se necessário
                if componente.formula_calculo:
                    # Avaliar fórmula (cuidado com segurança)
                    try:
                        tempo_padrao = eval(componente.formula_calculo.replace('diametro', str(diametro)))
                    except:
                        tempo_padrao = componente.tempo_padrao
            
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
                registro_id=apontamento.id,
                dados_depois={
                    'componente': componente.nome,
                    'modulo': modulo.nome,
                    'tempo_padrao': float(tempo_padrao)
                }
            )
            
            return JsonResponse({
                'success': True,
                'apontamento_id': apontamento.id,
                'componente_nome': componente.nome,
                'tempo_padrao': float(tempo_padrao),
                'inicio': apontamento.inicio_processo.strftime('%H:%M:%S')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def finalizar_componente(request):
    """Finaliza processo de soldagem de componente"""
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
            
            # Finalizar processo
            apontamento.fim_processo = timezone.now()
            
            # Calcular tempo real
            duracao = apontamento.fim_processo - apontamento.inicio_processo
            apontamento.tempo_real = duracao.total_seconds() / 60  # em minutos
            
            # Calcular eficiência
            if apontamento.tempo_real > 0:
                apontamento.eficiencia_calculada = (apontamento.tempo_padrao / apontamento.tempo_real) * 100
            else:
                apontamento.eficiencia_calculada = 100
            
            apontamento.save()
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario_id=soldador_id,
                acao='FINALIZAR_COMPONENTE',
                tabela_afetada='Apontamento',
                registro_id=apontamento.id,
                dados_depois={
                    'tempo_real': float(apontamento.tempo_real),
                    'eficiencia': float(apontamento.eficiencia_calculada)
                }
            )
            
            return JsonResponse({
                'success': True,
                'tempo_real': float(apontamento.tempo_real),
                'eficiencia': float(apontamento.eficiencia_calculada),
                'componente_nome': apontamento.componente.nome
            })
            
    except Apontamento.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Apontamento não encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# ==================== APIS DE PARADAS ====================

@csrf_exempt
def iniciar_parada(request):
    """Inicia uma parada (geral, manutenção ou qualidade)"""
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
            
            # Verificar se já existe parada em andamento
            parada_existente = Parada.objects.filter(
                soldador=soldador,
                fim__isnull=True
            ).first()
            
            if parada_existente:
                return JsonResponse({'success': False, 'message': 'Já existe uma parada em andamento'}, status=400)
            
            # Verificar senha especial se necessário
            usuario_autorizacao = None
            if tipo_parada.requer_senha_especial and senha_especial:
                # Verificar se é usuário de qualidade ou manutenção
                if tipo_parada.categoria == 'qualidade':
                    try:
                        usuario_qualidade = Usuario.objects.get(
                            username=senha_especial,
                            tipo_usuario='qualidade',
                            ativo=True
                        )
                        usuario_autorizacao = usuario_qualidade
                    except Usuario.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Senha de qualidade inválida'}, status=401)
                
                elif tipo_parada.categoria == 'manutencao':
                    try:
                        usuario_manutencao = Usuario.objects.get(
                            username=senha_especial,
                            tipo_usuario='manutencao',
                            ativo=True
                        )
                        usuario_autorizacao = usuario_manutencao
                    except Usuario.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Senha de manutenção inválida'}, status=401)
            
            # Pausar apontamento se houver um em andamento
            apontamento_pausado = Apontamento.objects.filter(
                soldador=soldador,
                fim_processo__isnull=True
            ).first()
            
            # Criar parada
            parada = Parada.objects.create(
                tipo_parada=tipo_parada,
                soldador=soldador,
                apontamento=apontamento_pausado,
                inicio=timezone.now(),
                motivo_detalhado=motivo_detalhado,
                usuario_autorizacao=usuario_autorizacao
            )
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario=soldador.usuario,
                acao='INICIAR_PARADA',
                tabela_afetada='Parada',
                registro_id=parada.id,
                dados_depois={
                    'tipo_parada': tipo_parada.nome,
                    'categoria': tipo_parada.categoria,
                    'motivo': motivo_detalhado
                }
            )
            
            return JsonResponse({
                'success': True,
                'parada_id': parada.id,
                'tipo_parada': tipo_parada.nome,
                'categoria': tipo_parada.categoria,
                'inicio': parada.inicio.strftime('%H:%M:%S')
            })
            
    except TipoParada.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Tipo de parada não encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def finalizar_parada(request):
    """Finaliza parada em andamento"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        with transaction.atomic():
            parada = Parada.objects.get(
                soldador_id=soldador_id,
                fim__isnull=True
            )
            
            # Finalizar parada
            parada.fim = timezone.now()
            duracao = parada.fim - parada.inicio
            parada.duracao_minutos = duracao.total_seconds() / 60
            parada.save()
            
            # Log de auditoria
            LogAuditoria.objects.create(
                usuario_id=soldador_id,
                acao='FINALIZAR_PARADA',
                tabela_afetada='Parada',
                registro_id=parada.id,
                dados_depois={
                    'tipo_parada': parada.tipo_parada.nome,
                    'duracao_minutos': float(parada.duracao_minutos)
                }
            )
            
            return JsonResponse({
                'success': True,
                'duracao_minutos': float(parada.duracao_minutos),
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
    """Painel de qualidade (placeholder)"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    # Implementar painel de qualidade completo
    return render(request, 'soldagem/painel_qualidade.html', {
        'titulo': 'Painel de Qualidade',
        'mensagem': 'Funcionalidade em desenvolvimento'
    })

def painel_paradas(request):
    """Painel de paradas (placeholder)"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    return render(request, 'soldagem/painel_paradas.html', {
        'titulo': 'Painel de Paradas',
        'mensagem': 'Funcionalidade em desenvolvimento'
    })

def painel_manutencao(request):
    """Painel de manutenção (placeholder)"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    return render(request, 'soldagem/painel_manutencao.html', {
        'titulo': 'Painel de Manutenção',
        'mensagem': 'Funcionalidade em desenvolvimento'
    })