#!/usr/bin/env python
"""
Criar painéis de qualidade, paradas e manutenção
Execute: python criar_paineis.py
"""

# 1. TEMPLATE APONTAMENTO.HTML sem debug
apontamento_template = '''{% extends 'base.html' %}

{% block title %}Apontamento - {{ soldador.usuario.nome_completo }}{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Saudação com relógio -->
    <div class="saudacao">
        <h3>{{ saudacao }}, {{ soldador.usuario.nome_completo }}!</h3>
        <div class="row mt-3">
            <div class="col-md-6">
                <strong>Data:</strong> {{ now|date:"d/m/Y" }}
            </div>
            <div class="col-md-6">
                <strong>Horário:</strong> <span id="hora-atual">{{ now|date:"H:i:s" }}</span>
            </div>
        </div>
    </div>
    
    <!-- Informações do pedido atual -->
    <div class="row mb-4" id="info-pedido" style="display: none;">
        <div class="col-md-12">
            <div class="alert alert-info text-center">
                <strong>Pedido: <span id="pedido-numero"></span> | Poste/Tubo: <span id="poste-numero"></span></strong>
            </div>
        </div>
    </div>
    
    <!-- Processo atual -->
    {% if apontamento_atual %}
    <div class="processo-atual">
        <h4>Soldando: {{ apontamento_atual.componente.nome }}</h4>
        <div class="tempo-decorrido" id="tempo-decorrido">00:00:00</div>
        <p>Tempo Padrão: {{ apontamento_atual.tempo_padrao }}min</p>
        
        <div class="mt-4">
            <button class="btn btn-processo btn-finalizar" onclick="finalizarComponente({{ apontamento_atual.id }})">
                ✓ ITEM FINALIZADO
            </button>
            <button class="btn btn-processo btn-qualidade" onclick="abrirQualidade()">
                QUALIDADE
            </button>
            <button class="btn btn-processo btn-manutencao" onclick="abrirManutencao()">
                MANUTENÇÃO
            </button>
            <button class="btn btn-processo btn-parada" onclick="abrirParadas()">
                PARADAS
            </button>
        </div>
    </div>
    {% else %}
    <!-- Menu principal -->
    <div class="row justify-content-center mt-4">
        <div class="col-md-8">
            <!-- Módulos principais -->
            <div class="row mb-4">
                {% for modulo in modulos %}
                <div class="col-md-6 col-lg-3 mb-3">
                    <button class="btn btn-modulo w-100" onclick="selecionarModulo({{ modulo.id }}, '{{ modulo.nome }}')">
                        {{ modulo.nome }}
                    </button>
                </div>
                {% endfor %}
            </div>
            
            <!-- Botões de ação -->
            <div class="row">
                <div class="col-md-4 mb-3">
                    <button class="btn btn-qualidade w-100" onclick="abrirQualidade()">
                        QUALIDADE
                    </button>
                </div>
                <div class="col-md-4 mb-3">
                    <button class="btn btn-parada w-100" onclick="abrirParadas()">
                        PARADAS
                    </button>
                </div>
                <div class="col-md-4 mb-3">
                    <button class="btn btn-manutencao w-100" onclick="abrirManutencao()">
                        MANUTENÇÃO
                    </button>
                </div>
            </div>
            
            <!-- Botão finalizar turno -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <button class="btn btn-outline-danger w-100" onclick="finalizarTurno()">
                        FINALIZAR TURNO
                    </button>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
</div>

<!-- Modal para dados do pedido -->
<div class="modal fade" id="modalPedido" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Dados do Pedido</h5>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label for="numero-pedido" class="form-label">Número do Pedido:</label>
                    <input type="text" class="form-control" id="numero-pedido" required>
                </div>
                <div class="mb-3">
                    <label for="numero-poste" class="form-label">Número do Poste/Tubo:</label>
                    <input type="text" class="form-control" id="numero-poste" required>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-danger" onclick="confirmarPedido()">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<!-- Modal para seleção de componentes -->
<div class="modal fade" id="modalComponentes" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Componentes do <span id="modulo-nome"></span></h5>
            </div>
            <div class="modal-body">
                <div class="row" id="lista-componentes">
                    <!-- Componentes serão carregados aqui -->
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Voltar</button>
            </div>
        </div>
    </div>
</div>

<!-- Modal para diâmetro -->
<div class="modal fade" id="modalDiametro" tabindex="-1">
    <div class="modal-dialog modal-sm">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Diâmetro do Tubo</h5>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label for="diametro" class="form-label">Diâmetro (mm):</label>
                    <input type="number" class="form-control form-control-lg text-center" 
                           id="diametro" min="1" max="1000" style="font-size: 1.5rem;">
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-danger" onclick="confirmarDiametro()">Confirmar</button>
            </div>
        </div>
    </div>
</div>

{% csrf_token %}

{% endblock %}

{% block extra_js %}
<script>
let moduloAtual = null;
let componenteSelecionado = null;
let timerInterval = null;

// Atualizar hora atual
function atualizarHora() {
    const now = new Date();
    document.getElementById('hora-atual').textContent = now.toLocaleTimeString('pt-BR');
}

setInterval(atualizarHora, 1000);

// Timer para processo atual
{% if apontamento_atual %}
function iniciarTimer() {
    const inicioProcesso = new Date('{{ apontamento_atual.inicio_processo|date:"c" }}');
    
    timerInterval = setInterval(() => {
        const agora = new Date();
        const diff = agora - inicioProcesso;
        
        const horas = Math.floor(diff / (1000 * 60 * 60));
        const minutos = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const segundos = Math.floor((diff % (1000 * 60)) / 1000);
        
        document.getElementById('tempo-decorrido').textContent = 
            `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
    }, 1000);
}

iniciarTimer();
{% endif %}

function selecionarModulo(moduloId, moduloNome) {
    moduloAtual = moduloId;
    document.getElementById('modulo-nome').textContent = moduloNome;
    
    const modal = new bootstrap.Modal(document.getElementById('modalPedido'));
    modal.show();
    
    setTimeout(() => {
        document.getElementById('numero-pedido').focus();
    }, 500);
}

function confirmarPedido() {
    const pedido = document.getElementById('numero-pedido').value;
    const poste = document.getElementById('numero-poste').value;
    
    if (!pedido.trim() || !poste.trim()) {
        alert('Preencha todos os campos');
        return;
    }
    
    bootstrap.Modal.getInstance(document.getElementById('modalPedido')).hide();
    
    document.getElementById('pedido-numero').textContent = pedido;
    document.getElementById('poste-numero').textContent = poste;
    document.getElementById('info-pedido').style.display = 'block';
    
    carregarComponentes(pedido, poste);
}

function carregarComponentes(pedido, poste) {
    const dados = {
        modulo_id: moduloAtual,
        pedido: pedido,
        poste: poste
    };
    
    fetch('/iniciar_modulo/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(dados)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const lista = document.getElementById('lista-componentes');
            lista.innerHTML = '';
            
            if (data.componentes && data.componentes.length > 0) {
                data.componentes.forEach(comp => {
                    const col = document.createElement('div');
                    col.className = 'col-md-6 col-lg-4 mb-3';
                    
                    const tempoTexto = comp.considera_diametro ? 
                        '(Diâmetro do tubo)' : 
                        `(${comp.tempo_padrao}min)`;
                    
                    col.innerHTML = `
                        <button class="btn btn-componente w-100" onclick="selecionarComponente(${comp.id}, '${comp.nome}', ${comp.considera_diametro})">
                            ${comp.nome}<br>
                            <small>${tempoTexto}</small>
                        </button>
                    `;
                    
                    lista.appendChild(col);
                });
                
                const modal = new bootstrap.Modal(document.getElementById('modalComponentes'));
                modal.show();
            } else {
                alert('Nenhum componente encontrado');
            }
        } else {
            alert(data.message || 'Erro ao carregar componentes');
        }
    })
    .catch(error => {
        alert(`Erro de conexão: ${error.message}`);
    });
}

function selecionarComponente(componenteId, componenteNome, consideraDiametro) {
    componenteSelecionado = componenteId;
    
    bootstrap.Modal.getInstance(document.getElementById('modalComponentes')).hide();
    
    if (consideraDiametro) {
        const modal = new bootstrap.Modal(document.getElementById('modalDiametro'));
        modal.show();
        
        setTimeout(() => {
            document.getElementById('diametro').focus();
        }, 500);
    } else {
        iniciarComponente(componenteId, null);
    }
}

function confirmarDiametro() {
    const diametro = document.getElementById('diametro').value;
    
    if (!diametro || diametro <= 0) {
        alert('Digite um diâmetro válido');
        return;
    }
    
    bootstrap.Modal.getInstance(document.getElementById('modalDiametro')).hide();
    
    iniciarComponente(componenteSelecionado, diametro);
}

function iniciarComponente(componenteId, diametro) {
    const dados = {
        componente_id: componenteId,
        diametro: diametro
    };
    
    fetch('/iniciar_componente/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(dados)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(`Componente iniciado: ${data.componente_nome}`);
            location.reload();
        } else {
            alert(data.message || 'Erro ao iniciar componente');
        }
    })
    .catch(error => {
        alert(`Erro: ${error.message}`);
    });
}

function finalizarComponente(apontamentoId) {
    if (!confirm('Finalizar este componente?')) return;
    
    const dados = {
        apontamento_id: apontamentoId
    };
    
    fetch('/finalizar_componente/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(dados)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(`Componente finalizado!\\nTempo real: ${data.tempo_real}min\\nEficiência: ${data.eficiencia}%`);
            location.reload();
        } else {
            alert(data.message || 'Erro ao finalizar componente');
        }
    })
    .catch(error => {
        alert(`Erro: ${error.message}`);
    });
}

function abrirQualidade() {
    window.location.href = '/painel_qualidade/';
}

function abrirParadas() {
    window.location.href = '/painel_paradas/';
}

function abrirManutencao() {
    window.location.href = '/painel_manutencao/';
}

function finalizarTurno() {
    if (confirm('Deseja finalizar o turno?')) {
        window.location.href = '/finalizar_turno/';
    }
}

function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    return token || '';
}

// Enter nos campos
document.getElementById('numero-pedido').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        document.getElementById('numero-poste').focus();
    }
});

document.getElementById('numero-poste').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        confirmarPedido();
    }
});

document.getElementById('diametro').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        confirmarDiametro();
    }
});
</script>
{% endblock %}'''

# 2. TEMPLATE PAINEL QUALIDADE
qualidade_template = '''{% extends 'base.html' %}

{% block title %}Painel de Qualidade{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="saudacao">
        <h3>Painel de Qualidade - {{ soldador.usuario.nome_completo }}</h3>
        <p>Aqui você pode registrar defeitos encontrados na soldagem</p>
    </div>
    
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5>🔍 Controle de Qualidade</h5>
                </div>
                <div class="card-body text-center">
                    <p class="mb-4">Funcionalidade em desenvolvimento</p>
                    <p>Em breve você poderá:</p>
                    <ul class="list-unstyled">
                        <li>• Registrar defeitos na soldagem</li>
                        <li>• Medir área dos defeitos</li>
                        <li>• Associar defeitos aos componentes</li>
                        <li>• Gerar relatórios de qualidade</li>
                    </ul>
                </div>
                <div class="card-footer">
                    <button class="btn btn-secondary" onclick="voltar()">⬅ Voltar</button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function voltar() {
    window.location.href = '/apontamento/';
}
</script>
{% endblock %}'''

# 3. TEMPLATE PAINEL PARADAS
paradas_template = '''{% extends 'base.html' %}

{% block title %}Painel de Paradas{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="saudacao">
        <h3>Painel de Paradas - {{ soldador.usuario.nome_completo }}</h3>
        <p>Registre paradas durante o processo de soldagem</p>
    </div>
    
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5>⏸️ Registro de Paradas</h5>
                </div>
                <div class="card-body text-center">
                    <p class="mb-4">Funcionalidade em desenvolvimento</p>
                    <p>Em breve você poderá registrar:</p>
                    <ul class="list-unstyled">
                        <li>• Ida ao banheiro</li>
                        <li>• Lanche/Almoço</li>
                        <li>• Troca de consumíveis</li>
                        <li>• Falta de material</li>
                        <li>• Reuniões</li>
                        <li>• Outras paradas operacionais</li>
                    </ul>
                </div>
                <div class="card-footer">
                    <button class="btn btn-secondary" onclick="voltar()">⬅ Voltar</button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function voltar() {
    window.location.href = '/apontamento/';
}
</script>
{% endblock %}'''

# 4. TEMPLATE PAINEL MANUTENÇÃO
manutencao_template = '''{% extends 'base.html' %}

{% block title %}Painel de Manutenção{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="saudacao">
        <h3>Painel de Manutenção - {{ soldador.usuario.nome_completo }}</h3>
        <p>Registre paradas para manutenção de equipamentos</p>
    </div>
    
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5>🔧 Manutenção de Equipamentos</h5>
                </div>
                <div class="card-body text-center">
                    <p class="mb-4">Funcionalidade em desenvolvimento</p>
                    <p>Em breve você poderá registrar:</p>
                    <ul class="list-unstyled">
                        <li>• Falhas de equipamento</li>
                        <li>• Manutenção preventiva</li>
                        <li>• Troca de eletrodos</li>
                        <li>• Regulagem de soldagem</li>
                        <li>• Limpeza de equipamentos</li>
                        <li>• Outras atividades de manutenção</li>
                    </ul>
                </div>
                <div class="card-footer">
                    <button class="btn btn-secondary" onclick="voltar()">⬅ Voltar</button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function voltar() {
    window.location.href = '/apontamento/';
}
</script>
{% endblock %}'''

# 5. TEMPLATE SELEÇÃO SOLDADOR sem debug
selecao_template = '''{% extends 'base.html' %}

{% block title %}Seleção de Soldador - OEE{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <h2 class="text-center mb-4" style="color: var(--primary-red);">
                Selecione o Soldador
            </h2>
            
            <div class="row">
                {% for soldador in soldadores %}
                <div class="col-md-6 col-lg-4">
                    <div class="soldador-card" onclick="selecionarSoldador({{ soldador.id }}, '{{ soldador.usuario.nome_completo }}')">
                        <div class="soldador-nome">{{ soldador.usuario.nome_completo }}</div>
                    </div>
                </div>
                {% empty %}
                <div class="col-12">
                    <div class="alert alert-warning text-center">
                        <h4>⚠️ Nenhum soldador encontrado!</h4>
                        <p>Execute: <code>python criar_dados_iniciais.py</code></p>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<!-- Modal para senha -->
<div class="modal fade" id="modalSenha" tabindex="-1">
    <div class="modal-dialog modal-sm">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Digite sua senha</h5>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label for="senha" class="form-label">Soldador: <strong><span id="soldador-nome"></span></strong></label>
                    <input type="password" class="form-control form-control-lg text-center" 
                           id="senha" maxlength="10" style="font-size: 1.5rem;" placeholder="Digite sua senha">
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-danger" onclick="confirmarLogin()">
                    <span id="spinner" style="display: none;">🔄</span>
                    Entrar
                </button>
            </div>
        </div>
    </div>
</div>

{% csrf_token %}

{% endblock %}

{% block extra_js %}
<script>
let soldadorSelecionado = null;

function selecionarSoldador(soldadorId, nome) {
    soldadorSelecionado = soldadorId;
    document.getElementById('soldador-nome').textContent = nome;
    document.getElementById('senha').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('modalSenha'));
    modal.show();
    
    setTimeout(() => {
        document.getElementById('senha').focus();
    }, 500);
}

function confirmarLogin() {
    const senha = document.getElementById('senha').value;
    
    if (!senha.trim()) {
        alert('Digite a senha');
        document.getElementById('senha').focus();
        return;
    }
    
    document.getElementById('spinner').style.display = 'inline-block';
    
    const dadosLogin = {
        soldador_id: soldadorSelecionado,
        senha: senha
    };
    
    fetch('/login_soldador/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(dadosLogin),
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('spinner').style.display = 'none';
        
        if (data.success) {
            window.location.href = data.redirect || '/apontamento/';
        } else {
            alert(`❌ Erro no login: ${data.message || 'Erro desconhecido'}`);
        }
    })
    .catch(error => {
        document.getElementById('spinner').style.display = 'none';
        alert(`❌ Erro de conexão: ${error.message}`);
    });
}

function getCsrfToken() {
    const metaTag = document.querySelector('[name=csrfmiddlewaretoken]');
    if (metaTag) {
        return metaTag.value;
    }
    
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    
    const hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (hiddenInput) {
        return hiddenInput.value;
    }
    
    return '';
}

// Enter para confirmar senha
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('senha').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            confirmarLogin();
        }
    });
});
</script>
{% endblock %}'''

# Escrever todos os templates
import os
os.makedirs('templates/soldagem', exist_ok=True)

templates = [
    ('templates/soldagem/apontamento.html', apontamento_template),
    ('templates/soldagem/painel_qualidade.html', qualidade_template),
    ('templates/soldagem/painel_paradas.html', paradas_template),
    ('templates/soldagem/painel_manutencao.html', manutencao_template),
    ('templates/soldagem/selecao_soldador.html', selecao_template),
]

for filename, content in templates:
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

print("✅ Templates criados:")
print("  - apontamento.html (sem debug)")
print("  - painel_qualidade.html")
print("  - painel_paradas.html") 
print("  - painel_manutencao.html")
print("  - selecao_soldador.html (sem debug)")

# 6. ATUALIZAR URLs
urls_content = '''from django.urls import path
from . import views

app_name = 'soldagem'

urlpatterns = [
    path('', views.selecao_soldador, name='selecao_soldador'),
    path('login_soldador/', views.login_soldador, name='login_soldador'),
    path('apontamento/', views.apontamento, name='apontamento'),
    path('iniciar_modulo/', views.iniciar_modulo, name='iniciar_modulo'),
    path('iniciar_componente/', views.iniciar_componente, name='iniciar_componente'),
    path('finalizar_componente/', views.finalizar_componente, name='finalizar_componente'),
    path('finalizar_turno/', views.finalizar_turno, name='finalizar_turno'),
    path('painel_qualidade/', views.painel_qualidade, name='painel_qualidade'),
    path('painel_paradas/', views.painel_paradas, name='painel_paradas'),
    path('painel_manutencao/', views.painel_manutencao, name='painel_manutencao'),
]
'''

with open('soldagem/urls.py', 'w', encoding='utf-8') as f:
    f.write(urls_content)

print("✅ URLs atualizadas com novos painéis")