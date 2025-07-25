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
            dados_depois={
                'soldador': soldador.usuario.nome_completo,
                'turno_id': turno.id
            }
        )
        
        return JsonResponse({
            'success': True,
            'redirect_url': '/soldagem/apontamento/',
            'soldador_nome': soldador.usuario.nome_completo
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
    
    try:
        soldador = Soldador.objects.get(id=soldador_id, ativo=True)
    except Soldador.DoesNotExist:
        request.session.flush()
        return redirect('soldagem:selecao_soldador')
    
    # Buscar dados necessários
    modulos = Modulo.objects.filter(ativo=True).order_by('ordem_exibicao')
    componentes = Componente.objects.filter(ativo=True).order_by('nome')
    
    # Verificar se há processo em andamento
    processo_ativo = Apontamento.objects.filter(
        soldador=soldador,
        fim_processo__isnull=True
    ).first()
    
    # Verificar se há parada em andamento
    parada_ativa = Parada.objects.filter(
        soldador=soldador,
        fim__isnull=True
    ).first()
    
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
        'componentes': componentes,
        'processo_ativo': processo_ativo,
        'parada_ativa': parada_ativa,
        'saudacao': saudacao,
        'agora': timezone.now()
    }
    
    return render(request, 'soldagem/apontamento.html', context)

def finalizar_turno(request):
    """Finaliza o turno do soldador"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    try:
        soldador = Soldador.objects.get(id=soldador_id)
        
        # Finalizar turno ativo
        turno_ativo = Turno.objects.filter(
            soldador=soldador,
            status='ativo'
        ).first()
        
        if turno_ativo:
            turno_ativo.fim_turno = timezone.now()
            turno_ativo.status = 'finalizado'
            turno_ativo.save()
        
        # Finalizar qualquer apontamento em andamento
        apontamentos_abertos = Apontamento.objects.filter(
            soldador=soldador,
            fim_processo__isnull=True
        )
        for apontamento in apontamentos_abertos:
            apontamento.fim_processo = timezone.now()
            apontamento.save()
        
        # Finalizar qualquer parada em andamento
        paradas_abertas = Parada.objects.filter(
            soldador=soldador,
            fim__isnull=True
        )
        for parada in paradas_abertas:
            parada.fim = timezone.now()
            parada.save()
        
        # Log de auditoria
        LogAuditoria.objects.create(
            usuario=soldador.usuario,
            acao='FINALIZAR_TURNO',
            tabela_afetada='Turno',
            registro_id=turno_ativo.id if turno_ativo else None,
            dados_depois={
                'soldador': soldador.usuario.nome_completo,
                'fim_turno': timezone.now().isoformat()
            }
        )
        
        # Limpar sessão
        request.session.flush()
        
        messages.success(request, 'Turno finalizado com sucesso!')
        
    except Exception as e:
        messages.error(request, f'Erro ao finalizar turno: {str(e)}')
    
    return redirect('soldagem:selecao_soldador')

# ==================== APIS DE APONTAMENTO ====================

@csrf_exempt
def iniciar_modulo(request):
    """Inicia processo de seleção de módulo"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        modulo_id = data.get('modulo_id')
        numero_pedido = data.get('numero_pedido')
        numero_poste_tubo = data.get('numero_poste_tubo')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        soldador = get_object_or_404(Soldador, id=soldador_id)
        modulo = get_object_or_404(Modulo, id=modulo_id, ativo=True)
        
        # Criar ou buscar pedido
        pedido, created = Pedido.objects.get_or_create(
            numero=numero_pedido,
            defaults={'descricao': f'Pedido {numero_pedido}'}
        )
        
        # Buscar componentes disponíveis
        componentes = Componente.objects.filter(ativo=True).order_by('nome')
        
        componentes_data = []
        for componente in componentes:
            componentes_data.append({
                'id': componente.id,
                'nome': componente.nome,
                'tempo_padrao': float(componente.tempo_padrao),
                'considera_diametro': componente.considera_diametro
            })
        
        # Salvar dados na sessão para usar no próximo step
        request.session['processo_temp'] = {
            'modulo_id': modulo.id,
            'pedido_id': pedido.id,
            'numero_poste_tubo': numero_poste_tubo
        }
        request.session.save()
        
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
    """Inicia processo de soldagem de um componente"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        componente_id = data.get('componente_id')
        diametro = data.get('diametro')
        
        soldador_id = request.session.get('soldador_id')
        processo_temp = request.session.get('processo_temp')
        
        if not soldador_id or not processo_temp:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        soldador = get_object_or_404(Soldador, id=soldador_id)
        componente = get_object_or_404(Componente, id=componente_id, ativo=True)
        modulo = get_object_or_404(Modulo, id=processo_temp['modulo_id'])
        pedido = get_object_or_404(Pedido, id=processo_temp['pedido_id'])
        
        # Verificar se já existe processo em andamento
        processo_existente = Apontamento.objects.filter(
            soldador=soldador,
            fim_processo__isnull=True
        ).first()
        
        if processo_existente:
            return JsonResponse({'success': False, 'message': 'Já existe um processo em andamento'}, status=400)
        
        # Calcular tempo padrão (considerando diâmetro se necessário)
        tempo_padrao = componente.tempo_padrao
        if componente.considera_diametro and diametro:
            # Aqui você pode implementar a fórmula específica
            # Por enquanto, usar o tempo padrão base
            pass
        
        # Criar apontamento
        with transaction.atomic():
            apontamento = Apontamento.objects.create(
                soldador=soldador,
                modulo=modulo,
                componente=componente,
                pedido=pedido,
                numero_poste_tubo=processo_temp['numero_poste_tubo'],
                diametro=diametro if diametro else None,
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
                    'pedido': pedido.numero,
                    'numero_poste_tubo': processo_temp['numero_poste_tubo']
                }
            )
        
        # Limpar dados temporários
        if 'processo_temp' in request.session:
            del request.session['processo_temp']
            request.session.save()
        
        return JsonResponse({
            'success': True,
            'apontamento_id': apontamento.id,
            'componente_nome': componente.nome,
            'tempo_padrao': float(tempo_padrao),
            'inicio': apontamento.inicio_processo.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def finalizar_componente(request):
    """Finaliza processo de soldagem do componente"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        apontamento_id = data.get('apontamento_id')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        soldador = get_object_or_404(Soldador, id=soldador_id)
        apontamento = get_object_or_404(Apontamento, id=apontamento_id, soldador=soldador)
        
        if apontamento.fim_processo:
            return JsonResponse({'success': False, 'message': 'Processo já finalizado'}, status=400)
        
        # Finalizar apontamento
        apontamento.fim_processo = timezone.now()
        apontamento.save()  # O save() calcula automaticamente tempo_real e eficiência
        
        # Log de auditoria
        LogAuditoria.objects.create(
            usuario=soldador.usuario,
            acao='FINALIZAR_COMPONENTE',
            tabela_afetada='Apontamento',
            registro_id=apontamento.id,
            dados_depois={
                'componente': apontamento.componente.nome,
                'tempo_real': float(apontamento.tempo_real) if apontamento.tempo_real else 0,
                'eficiencia': float(apontamento.eficiencia_calculada) if apontamento.eficiencia_calculada else 0
            }
        )
        
        return JsonResponse({
            'success': True,
            'tempo_real': float(apontamento.tempo_real) if apontamento.tempo_real else 0,
            'eficiencia': float(apontamento.eficiencia_calculada) if apontamento.eficiencia_calculada else 0
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# ==================== APIS DE PARADAS ====================

@csrf_exempt
def iniciar_parada(request):
    """Inicia uma parada"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        tipo_parada_id = data.get('tipo_parada_id')
        motivo_detalhado = data.get('motivo_detalhado', '')
        senha_especial = data.get('senha_especial', '')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        soldador = get_object_or_404(Soldador, id=soldador_id)
        tipo_parada = get_object_or_404(TipoParada, id=tipo_parada_id, ativo=True)
        
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
            # CORREÇÃO: Verificar senha corretamente
            if tipo_parada.categoria == 'qualidade':
                try:
                    usuarios_qualidade = Usuario.objects.filter(
                        tipo_usuario='qualidade',
                        ativo=True
                    )
                    usuario_autorizacao = None
                    for usuario in usuarios_qualidade:
                        if check_password(senha_especial, usuario.password):
                            usuario_autorizacao = usuario
                            break
                    
                    if not usuario_autorizacao:
                        return JsonResponse({'success': False, 'message': 'Senha de qualidade inválida'}, status=401)
                        
                except Exception:
                    return JsonResponse({'success': False, 'message': 'Erro na validação da senha de qualidade'}, status=401)
            
            elif tipo_parada.categoria == 'manutencao':
                try:
                    usuarios_manutencao = Usuario.objects.filter(
                        tipo_usuario='manutencao',
                        ativo=True
                    )
                    usuario_autorizacao = None
                    for usuario in usuarios_manutencao:
                        if check_password(senha_especial, usuario.password):
                            usuario_autorizacao = usuario
                            break
                    
                    if not usuario_autorizacao:
                        return JsonResponse({'success': False, 'message': 'Senha de manutenção inválida'}, status=401)
                        
                except Exception:
                    return JsonResponse({'success': False, 'message': 'Erro na validação da senha de manutenção'}, status=401)
        
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
                'usuario_autorizacao': usuario_autorizacao.username if usuario_autorizacao else None
            }
        )
        
        return JsonResponse({
            'success': True,
            'parada_id': parada.id,
            'tipo_parada': tipo_parada.nome,
            'inicio': parada.inicio.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def finalizar_parada(request):
    """Finaliza uma parada"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        parada_id = data.get('parada_id')
        
        soldador_id = request.session.get('soldador_id')
        if not soldador_id:
            return JsonResponse({'success': False, 'message': 'Sessão expirada'}, status=401)
        
        soldador = get_object_or_404(Soldador, id=soldador_id)
        parada = get_object_or_404(Parada, id=parada_id, soldador=soldador)
        
        if parada.fim:
            return JsonResponse({'success': False, 'message': 'Parada já finalizada'}, status=400)
        
        # Finalizar parada
        parada.fim = timezone.now()
        parada.save()  # O save() calcula automaticamente a duração
        
        # Log de auditoria
        LogAuditoria.objects.create(
            usuario=soldador.usuario,
            acao='FINALIZAR_PARADA',
            tabela_afetada='Parada',
            registro_id=parada.id,
            dados_depois={
                'tipo_parada': parada.tipo_parada.nome,
                'duracao_minutos': float(parada.duracao_minutos) if parada.duracao_minutos else 0
            }
        )
        
        return JsonResponse({
            'success': True,
            'duracao_minutos': float(parada.duracao_minutos) if parada.duracao_minutos else 0,
            'message': 'Parada finalizada com sucesso'
        })
        
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
    
    # Implementar painel de qualidade completo
    return render(request, 'soldagem/painel_qualidade.html', {
        'titulo': 'Painel de Qualidade',
        'mensagem': 'Funcionalidade em desenvolvimento'
    })

def painel_paradas(request):
    """Painel de paradas"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    return render(request, 'soldagem/painel_paradas.html', {
        'titulo': 'Painel de Paradas',
        'mensagem': 'Funcionalidade em desenvolvimento'
    })

def painel_manutencao(request):
    """Painel de manutenção"""
    soldador_id = request.session.get('soldador_id')
    if not soldador_id:
        return redirect('soldagem:selecao_soldador')
    
    return render(request, 'soldagem/painel_manutencao.html', {
        'titulo': 'Painel de Manutenção',
        'mensagem': 'Funcionalidade em desenvolvimento'
    })

# ADICIONAR ao final do arquivo views.py

@csrf_exempt
def status_conexao(request):
    """API para verificar status de conexão"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        # Fazer uma consulta simples no banco para verificar conectividade
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            'success': True,
            'status': 'online',
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'status': 'offline',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)