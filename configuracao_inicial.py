# Execute: python manage.py shell < configuracao_inicial.py

import os
import django
from django.contrib.auth.hashers import make_password

print("🚀 Iniciando configuração inicial do sistema OEE...")

# CORRIGIR: Importar TUDO do soldagem
from soldagem.models import Usuario, Soldador, Modulo, Componente, TipoParada
from qualidade.models import TipoDefeito

# 1. CRIAR USUÁRIOS BÁSICOS
print("👤 Criando usuários...")

# Admin
admin_user, created = Usuario.objects.get_or_create(
    username='admin',
    defaults={
        'password': make_password('admin123'),
        'email': 'admin@empresa.com',
        'nome_completo': 'Administrador do Sistema',
        'tipo_usuario': 'admin',
        'ativo': True
    }
)
if created:
    print("✅ Usuário admin criado (admin/admin123)")

# Qualidade
qualidade_user, created = Usuario.objects.get_or_create(
    username='qualidade',
    defaults={
        'password': make_password('qual123'),
        'email': 'qualidade@empresa.com',
        'nome_completo': 'Controle de Qualidade',
        'tipo_usuario': 'qualidade',
        'ativo': True
    }
)
if created:
    print("✅ Usuário qualidade criado (qualidade/qual123)")

# Manutenção
manutencao_user, created = Usuario.objects.get_or_create(
    username='manutencao',
    defaults={
        'password': make_password('manut123'),
        'email': 'manutencao@empresa.com',
        'nome_completo': 'Equipe de Manutenção',
        'tipo_usuario': 'manutencao',
        'ativo': True
    }
)
if created:
    print("✅ Usuário manutenção criado (manutencao/manut123)")

# 2. CRIAR SOLDADORES DE EXEMPLO
print("🔧 Criando soldadores...")

soldadores_data = [
    {'nome': 'João Silva', 'usuario': 'joao', 'senha': '1234'},
    {'nome': 'Maria Santos', 'usuario': 'maria', 'senha': '5678'},
    {'nome': 'Pedro Oliveira', 'usuario': 'pedro', 'senha': '9012'},
    {'nome': 'Ana Costa', 'usuario': 'ana', 'senha': '3456'},
]

for data in soldadores_data:
    # Criar usuário
    usuario, created = Usuario.objects.get_or_create(
        username=data['usuario'],
        defaults={
            'password': make_password('senha123'),
            'email': f"{data['usuario']}@empresa.com",
            'nome_completo': data['nome'],
            'tipo_usuario': 'soldador',
            'ativo': True
        }
    )
    
    # Criar soldador
    soldador, created = Soldador.objects.get_or_create(
        usuario=usuario,
        defaults={
            'senha_simplificada': data['senha'],
            'ativo': True
        }
    )
    
    if created:
        print(f"✅ Soldador {data['nome']} criado (senha: {data['senha']})")

# 3. CRIAR MÓDULOS
print("🏭 Criando módulos...")

modulos_data = [
    {'nome': 'Módulo A', 'ordem': 1},
    {'nome': 'Módulo T', 'ordem': 2},
    {'nome': 'Módulo B', 'ordem': 3},
    {'nome': 'Módulo C', 'ordem': 4},
]

for data in modulos_data:
    modulo, created = Modulo.objects.get_or_create(
        nome=data['nome'],
        defaults={
            'descricao': f'Módulo de soldagem {data["nome"]}',
            'ordem_exibicao': data['ordem'],
            'ativo': True
        }
    )
    if created:
        print(f"✅ {data['nome']} criado")

# 4. CRIAR COMPONENTES
print("⚙️ Criando componentes...")

componentes_data = [
    {'nome': 'CHAPA DA CRUZETA', 'tempo': 15.0, 'diametro': False},
    {'nome': 'FAIS', 'tempo': 8.0, 'diametro': False},
    {'nome': 'SUPORTE DE FIXAÇÃO', 'tempo': 12.0, 'diametro': False},
    {'nome': 'BRAÇADEIRA', 'tempo': 6.0, 'diametro': False},
    {'nome': 'TUBO PRINCIPAL', 'tempo': 20.0, 'diametro': True, 'formula': 'diametro * 0.5 + 10'},
    {'nome': 'CONEXÃO LATERAL', 'tempo': 10.0, 'diametro': False},
]

for data in componentes_data:
    componente, created = Componente.objects.get_or_create(
        nome=data['nome'],
        defaults={
            'descricao': f'Componente {data["nome"]} para soldagem',
            'tempo_padrao': data['tempo'],
            'considera_diametro': data.get('diametro', False),
            'formula_calculo': data.get('formula'),
            'ativo': True
        }
    )
    if created:
        print(f"✅ Componente {data['nome']} criado ({data['tempo']} min)")

# 5. CRIAR TIPOS DE PARADA
print("⏸️ Criando tipos de parada...")

paradas_data = [
    # Paradas gerais
    {'nome': 'Higiene Pessoal', 'categoria': 'geral', 'penaliza': True},
    {'nome': 'Troca de Consumíveis', 'categoria': 'geral', 'penaliza': True},
    {'nome': 'Falta de Material', 'categoria': 'geral', 'penaliza': False},
    {'nome': 'Aguardando Liberação', 'categoria': 'geral', 'penaliza': False},
    {'nome': 'Intervalo', 'categoria': 'geral', 'penaliza': False},
    
    # Paradas de manutenção
    {'nome': 'Manutenção Preventiva', 'categoria': 'manutencao', 'penaliza': False, 'senha': True},
    {'nome': 'Manutenção Corretiva', 'categoria': 'manutencao', 'penaliza': False, 'senha': True},
    {'nome': 'Ajuste de Equipamento', 'categoria': 'manutencao', 'penaliza': True, 'senha': True},
    
    # Paradas de qualidade
    {'nome': 'Inspeção de Qualidade', 'categoria': 'qualidade', 'penaliza': False, 'senha': True},
    {'nome': 'Retrabalho', 'categoria': 'qualidade', 'penaliza': True, 'senha': True},
]

cores = {
    'geral': '#6c757d',
    'manutencao': '#ffc107', 
    'qualidade': '#dc3545'
}

for data in paradas_data:
    tipo, created = TipoParada.objects.get_or_create(
        nome=data['nome'],
        categoria=data['categoria'],
        defaults={
            'penaliza_oee': data['penaliza'],
            'requer_senha_especial': data.get('senha', False),
            'cor_exibicao': cores[data['categoria']],
            'ativo': True
        }
    )
    if created:
        print(f"✅ Tipo de parada {data['nome']} ({data['categoria']})")

# 6. CRIAR TIPOS DE DEFEITO
print("🔍 Criando tipos de defeito...")

defeitos_data = [
    {'nome': 'Porosidade', 'cor': '#dc3545'},
    {'nome': 'Falta de Fusão', 'cor': '#fd7e14'},
    {'nome': 'Inclusão de Escória', 'cor': '#ffc107'},
    {'nome': 'Mordedura', 'cor': '#20c997'},
    {'nome': 'Perfuração', 'cor': '#6f42c1'},
    {'nome': 'Sobreposição', 'cor': '#e83e8c'},
]

for data in defeitos_data:
    defeito, created = TipoDefeito.objects.get_or_create(
        nome=data['nome'],
        defaults={
            'descricao': f'Defeito de soldagem: {data["nome"]}',
            'cor_exibicao': data['cor'],
            'ativo': True
        }
    )
    if created:
        print(f"✅ Tipo de defeito {data['nome']}")

print("\n" + "="*50)
print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
print("="*50)
print("👤 USUÁRIOS CRIADOS:")
print("   Admin: admin / admin123")
print("   Qualidade: qualidade / qual123")
print("   Manutenção: manutencao / manut123")
print("\n🔧 SOLDADORES CRIADOS:")
print("   João Silva - Senha: 1234")
print("   Maria Santos - Senha: 5678")
print("   Pedro Oliveira - Senha: 9012")
print("   Ana Costa - Senha: 3456")
print("\n🏭 MÓDULOS: A, T, B, C")
print("⚙️ COMPONENTES: 6 tipos cadastrados")
print("⏸️ PARADAS: 10 tipos (geral, manutenção, qualidade)")
print("🔍 DEFEITOS: 6 tipos cadastrados")
print("\n📱 Sistema pronto para uso!")
print("🌐 Acesse: http://localhost:8000/soldagem/")