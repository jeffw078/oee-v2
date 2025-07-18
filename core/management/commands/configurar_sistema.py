from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Soldador, Modulo, Componente, ConfiguracaoSistema
from soldagem.models import TipoParada
from qualidade.models import TipoDefeito

User = get_user_model()

class Command(BaseCommand):
    help = 'Configuração inicial do sistema OEE'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando configuração do sistema OEE...')
        
        # Criar usuário admin
        self.criar_usuario_admin()
        
        # Criar módulos
        self.criar_modulos()
        
        # Criar componentes
        self.criar_componentes()
        
        # Criar tipos de parada
        self.criar_tipos_parada()
        
        # Criar tipos de defeito
        self.criar_tipos_defeito()
        
        # Configurações do sistema
        self.criar_configuracoes()
        
        self.stdout.write(self.style.SUCCESS('✅ Sistema configurado com sucesso!'))
        self.stdout.write('👤 Admin criado: admin / admin123')
        self.stdout.write('🔧 Dados iniciais carregados')
        self.stdout.write('📱 Sistema pronto para uso!')

    def criar_usuario_admin(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                password='admin123',
                nome_completo='Administrador do Sistema',
                tipo_usuario='admin'
            )
            self.stdout.write('✓ Usuário admin criado')

    def criar_modulos(self):
        modulos = [
            ('MÓDULO A', 'Módulo A de soldagem', 1),
            ('MÓDULO T', 'Módulo T de soldagem', 2),
            ('MÓDULO B', 'Módulo B de soldagem', 3),
            ('MÓDULO C', 'Módulo C de soldagem', 4),
        ]
        
        for nome, descricao, ordem in modulos:
            modulo, created = Modulo.objects.get_or_create(
                nome=nome,
                defaults={
                    'descricao': descricao,
                    'ordem_exibicao': ordem,
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✓ Módulo criado: {nome}')

    def criar_componentes(self):
        componentes = [
            # Componentes com diâmetro
            ('FAIS', 'Solda FAIS', 0, True, 'diametro * 0.05'),
            ('FAIB', 'Solda FAIB', 0, True, 'diametro * 0.04'),
            ('CHAPA DA CRUZETA', 'Soldagem da chapa da cruzeta', 0, True, 'diametro * 0.03'),
            ('CHAPA DE SACRIFÍCIO', 'Chapa de sacrifício', 0, True, 'diametro * 0.02'),
            ('FAES', 'Solda FAES', 0, True, 'diametro * 0.035'),
            ('FAIE', 'Solda FAIE', 0, True, 'diametro * 0.025'),
            
            # Componentes fixos
            ('ANTIGIRIO', 'Soldagem antigirio', 60, False, ''),
            ('ATERRAMENTO', 'Aterramento do poste', 20, False, ''),
            ('OLHAL LINHA DE VIDA', 'Olhal para linha de vida', 18, False, ''),
            ('ESCADAS', 'Soldagem de escadas', 108, False, ''),
            ('MÃO FRANCESA', 'Soldagem mão francesa', 40, False, ''),
            ('BASE ISOLADORA', 'Base isoladora', 95, False, ''),
            ('OLHAIS DE FASE', 'Olhais de fase', 33, False, ''),
            ('APOIO DE PÉ E MÃO', 'Apoio de pé e mão', 60, False, ''),
            ('OLHAL DE IÇAMENTO', 'Olhal de içamento', 25, False, ''),
        ]
        
        for nome, descricao, tempo_padrao, considera_diametro, formula in componentes:
            componente, created = Componente.objects.get_or_create(
                nome=nome,
                defaults={
                    'descricao': descricao,
                    'tempo_padrao': tempo_padrao,
                    'considera_diametro': considera_diametro,
                    'formula_calculo': formula,
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✓ Componente criado: {nome}')

    def criar_tipos_parada(self):
        tipos_parada = [
            # Paradas gerais
            ('Ida ao Banheiro', 'geral', True, False, '#ffc107'),
            ('Lanche/Almoço', 'geral', False, False, '#28a745'),
            ('Troca de Consumíveis', 'geral', True, False, '#17a2b8'),
            ('Falta de Material', 'geral', False, False, '#6c757d'),
            ('Reunião', 'geral', False, False, '#20c997'),
            
            # Paradas de manutenção
            ('Falha de Equipamento', 'manutencao', True, True, '#dc3545'),
            ('Manutenção Preventiva', 'manutencao', False, True, '#fd7e14'),
            ('Troca de Eletrodo', 'manutencao', True, False, '#20c997'),
            ('Regulagem de Soldagem', 'manutencao', True, True, '#6f42c1'),
            
            # Paradas de qualidade
            ('Avaliação de Qualidade', 'qualidade', False, True, '#007bff'),
            ('Retrabalho', 'qualidade', True, True, '#dc3545'),
            ('Inspeção Dimensional', 'qualidade', False, True, '#17a2b8'),
        ]
        
        for nome, categoria, penaliza_oee, requer_senha, cor in tipos_parada:
            tipo, created = TipoParada.objects.get_or_create(
                nome=nome,
                defaults={
                    'categoria': categoria,
                    'penaliza_oee': penaliza_oee,
                    'requer_senha_especial': requer_senha,
                    'cor_exibicao': cor,
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✓ Tipo de parada criado: {nome}')

    def criar_tipos_defeito(self):
        tipos_defeito = [
            ('Porosidade', 'Poros na soldagem', '#ffc107'),
            ('Desalinhamento', 'Solda fora de posição', '#dc3545'),
            ('Falta de Penetração', 'Penetração insuficiente', '#e83e8c'),
            ('Respingo Excessivo', 'Excesso de respingos', '#fd7e14'),
            ('Mordedura', 'Mordedura na soldagem', '#6f42c1'),
            ('Trinca', 'Trinca na solda', '#dc3545'),
            ('Inclusão de Escória', 'Escória na soldagem', '#6c757d'),
        ]
        
        for nome, descricao, cor in tipos_defeito:
            tipo, created = TipoDefeito.objects.get_or_create(
                nome=nome,
                defaults={
                    'descricao': descricao,
                    'cor_exibicao': cor,
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✓ Tipo de defeito criado: {nome}')

    def criar_configuracoes(self):
        configs = [
            ('horas_trabalho_padrao', '8.0', 'Horas de trabalho padrão por dia', 'float'),
            ('senha_qualidade', 'QUAL123', 'Senha especial para qualidade', 'string'),
            ('senha_manutencao', 'MANUT456', 'Senha especial para manutenção', 'string'),
            ('backup_automatico', 'true', 'Backup automático ativado', 'boolean'),
            ('versao_sistema', '1.0.0', 'Versão atual do sistema', 'string'),
        ]
        
        for chave, valor, descricao, tipo_dado in configs:
            config, created = ConfiguracaoSistema.objects.get_or_create(
                chave=chave,
                defaults={
                    'valor': valor,
                    'descricao': descricao,
                    'tipo_dado': tipo_dado
                }
            )
            if created:
                self.stdout.write(f'✓ Configuração criada: {chave}')