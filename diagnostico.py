# correcao_rapida.py - Execute: python correcao_rapida.py

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oee_system.settings')
django.setup()

def corrigir_sistema():
    print("🔧 Iniciando correção do sistema...")
    
    # 1. Corrigir URLs
    urls_content = '''from django.urls import path
from . import views

app_name = 'soldagem'

urlpatterns = [
    # URLs principais
    path('', views.selecao_soldador, name='selecao_soldador'),
    path('login_soldador/', views.login_soldador, name='login_soldador'),
    path('apontamento/', views.apontamento, name='apontamento'),
    path('finalizar_turno/', views.finalizar_turno, name='finalizar_turno'),
    
    # APIs de apontamento
    path('api/iniciar_modulo/', views.iniciar_modulo, name='iniciar_modulo'),
    path('api/iniciar_componente/', views.iniciar_componente, name='iniciar_componente'),
    path('api/finalizar_componente/', views.finalizar_componente, name='finalizar_componente'),
    
    # APIs de paradas
    path('api/iniciar_parada/', views.iniciar_parada, name='iniciar_parada'),
    path('api/finalizar_parada/', views.finalizar_parada, name='finalizar_parada'),
    path('api/buscar_tipos_parada/', views.buscar_tipos_parada, name='buscar_tipos_parada'),
    
    # Painéis específicos
    path('painel_qualidade/', views.painel_qualidade, name='painel_qualidade'),
    path('painel_paradas/', views.painel_paradas, name='painel_paradas'),
    path('painel_manutencao/', views.painel_manutencao, name='painel_manutencao'),
]
'''
    
    with open('soldagem/urls.py', 'w', encoding='utf-8') as f:
        f.write(urls_content)
    print("✅ URLs corrigidas")
    
    # 2. Criar módulos se não existirem
    try:
        from core.models import Modulo
    except ImportError:
        from soldagem.models import Modulo
    
    if Modulo.objects.count() == 0:
        Modulo.objects.create(nome='Módulo A', ordem_exibicao=1)
        Modulo.objects.create(nome='Módulo T', ordem_exibicao=2)
        Modulo.objects.create(nome='Módulo B', ordem_exibicao=3)
        Modulo.objects.create(nome='Módulo C', ordem_exibicao=4)
        print("✅ Módulos criados")
    
    # 3. Criar tipos de parada se não existirem
    from soldagem.models import TipoParada
    if TipoParada.objects.count() == 0:
        TipoParada.objects.create(
            nome='Higiene Pessoal',
            categoria='geral',
            penaliza_oee=True,
            requer_senha_especial=False,
            cor_exibicao='#6c757d'
        )
        TipoParada.objects.create(
            nome='Inspeção de Qualidade',
            categoria='qualidade',
            penaliza_oee=False,
            requer_senha_especial=True,
            cor_exibicao='#28a745'
        )
        TipoParada.objects.create(
            nome='Manutenção Preventiva',
            categoria='manutencao',
            penaliza_oee=False,
            requer_senha_especial=True,
            cor_exibicao='#ffc107'
        )
        print("✅ Tipos de parada criados")
    
    print("🎉 Correção concluída! Reinicie o servidor e teste.")

if __name__ == "__main__":
    corrigir_sistema()