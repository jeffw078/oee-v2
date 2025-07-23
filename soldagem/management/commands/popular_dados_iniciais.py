# soldagem/management/commands/popular_dados_iniciais.py

from django.core.management.base import BaseCommand
from django.db import transaction
from soldagem.models import TipoParada
from qualidade.models import TipoDefeito
from soldagem.models import Usuario, Soldador, Modulo, Componente

class Command(BaseCommand):
    help = 'Popula banco de dados com dados iniciais para demonstração'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('🚀 Iniciando população de dados iniciais...')
            
            # 1. TIPOS DE PARADA GERAIS
            self.stdout.write('📋 Criando tipos de parada gerais...')
            tipos_parada_gerais = [
                {
                    'nome': 'Higiene Pessoal',
                    'categoria': 'geral',
                    'penaliza_oee': True,
                    'requer_senha_especial': False,
                    'cor_exibicao': '#6c757d'
                },
                {
                    'nome': 'Troca de Consumíveis',
                    'categoria': 'geral',
                    'penaliza_oee': True,
                    'requer_senha_especial': False,
                    'cor_exibicao': '#17a2b8'
                },
                {
                    'nome': 'Limpeza do Posto',
                    'categoria': 'geral',
                    'penaliza_oee': True,
                    'requer_senha_especial': False,
                    'cor_exibicao': '#28a745'
                },
                {
                    'nome': 'Falta de Material',
                    'categoria': 'geral',
                    'penaliza_oee': False,  # Não penaliza OEE
                    'requer_senha_especial': False,
                    'cor_exibicao': '#fd7e14'
                },
                {
                    'nome': 'Reunião/Treinamento',
                    'categoria': 'geral',
                    'penaliza_oee': False,  # Não penaliza OEE
                    'requer_senha_especial': False,
                    'cor_exibicao': '#6f42c1'
                },
                {
                    'nome': 'Problema de Setup',
                    'categoria': 'geral',
                    'penaliza_oee': True,
                    'requer_senha_especial': False,
                    'cor_exibicao': '#dc3545'
                }
            ]
            
            for tipo_data in tipos_parada_gerais:
                tipo, created = TipoParada.objects.get_or_create(
                    nome=tipo_data['nome'],
                    categoria=tipo_data['categoria'],
                    defaults=tipo_data
                )
                if created:
                    self.stdout.write(f'  ✅ Criado: {tipo.nome}')
                else:
                    self.stdout.write(f'  ⚠️  Já existe: {tipo.nome}')
            
            # 2. TIPOS DE PARADA DE MANUTENÇÃO
            self.stdout.write('🔧 Criando tipos de parada de manutenção...')
            tipos_parada_manutencao = [
                {
                    'nome': 'Manutenção Preventiva',
                    'categoria': 'manutencao',
                    'penaliza_oee': False,  # Não penaliza OEE
                    'requer_senha_especial': True,
                    'cor_exibicao': '#28a745'
                },
                {
                    'nome': 'Falha de Equipamento',
                    'categoria': 'manutencao',
                    'penaliza_oee': True,
                    'requer_senha_especial': True,
                    'cor_exibicao': '#dc3545'
                },
                {
                    'nome': 'Problema Elétrico',
                    'categoria': 'manutencao',
                    'penaliza_oee': True,
                    'requer_senha_especial': True,
                    'cor_exibicao': '#ffc107'
                },
                {
                    'nome': 'Problema de Gás',
                    'categoria': 'manutencao',
                    'penaliza_oee': True,
                    'requer_senha_especial': True,
                    'cor_exibicao': '#17a2b8'
                },
                {
                    'nome': 'Calibração de Equipamento',
                    'categoria': 'manutencao',
                    'penaliza_oee': False,  # Não penaliza OEE
                    'requer_senha_especial': True,
                    'cor_exibicao': '#6f42c1'
                },
                {
                    'nome': 'Troca de Peças/Componentes',
                    'categoria': 'manutencao',
                    'penaliza_oee': True,
                    'requer_senha_especial': True,
                    'cor_exibicao': '#fd7e14'
                }
            ]
            
            for tipo_data in tipos_parada_manutencao:
                tipo, created = TipoParada.objects.get_or_create(
                    nome=tipo_data['nome'],
                    categoria=tipo_data['categoria'],
                    defaults=tipo_data
                )
                if created:
                    self.stdout.write(f'  ✅ Criado: {tipo.nome}')
                else:
                    self.stdout.write(f'  ⚠️  Já existe: {tipo.nome}')
            
            # 3. TIPOS DE PARADA DE QUALIDADE
            self.stdout.write('🔍 Criando tipos de parada de qualidade...')
            tipos_parada_qualidade = [
                {
                    'nome': 'Inspeção de Qualidade',
                    'categoria': 'qualidade',
                    'penaliza_oee': False,  # Não penaliza OEE
                    'requer_senha_especial': True,
                    'cor_exibicao': '#28a745'
                },
                {
                    'nome': 'Retrabalho por Defeito',
                    'categoria': 'qualidade',
                    'penaliza_oee': True,
                    'requer_senha_especial': True,
                    'cor_exibicao': '#dc3545'
                },
                {
                    'nome': 'Auditoria de Processo',
                    'categoria': 'qualidade',
                    'penaliza_oee': False,  # Não penaliza OEE
                    'requer_senha_especial': True,
                    'cor_exibicao': '#17a2b8'
                }
            ]
            
            for tipo_data in tipos_parada_qualidade:
                tipo, created = TipoParada.objects.get_or_create(
                    nome=tipo_data['nome'],
                    categoria=tipo_data['categoria'],
                    defaults=tipo_data
                )
                if created:
                    self.stdout.write(f'  ✅ Criado: {tipo.nome}')
                else:
                    self.stdout.write(f'  ⚠️  Já existe: {tipo.nome}')
            
            # 4. TIPOS DE DEFEITO
            self.stdout.write('🚨 Criando tipos de defeito...')
            tipos_defeito = [
                {
                    'nome': 'Porosidade',
                    'descricao': 'Presença de bolhas ou cavidades na solda',
                    'cor_exibicao': '#dc3545'
                },
                {
                    'nome': 'Falta de Penetração',
                    'descricao': 'Solda não penetrou adequadamente no material',
                    'cor_exibicao': '#fd7e14'
                },
                {
                    'nome': 'Inclusão de Escória',
                    'descricao': 'Restos de escória incorporados na solda',
                    'cor_exibicao': '#6c757d'
                },
                {
                    'nome': 'Trinca',
                    'descricao': 'Fissura ou rachadura na solda',
                    'cor_exibicao': '#721c24'
                },
                {
                    'nome': 'Mordedura',
                    'descricao': 'Entalhe no metal base junto ao cordão de solda',
                    'cor_exibicao': '#ffc107'
                },
                {
                    'nome': 'Respingo Excessivo',
                    'descricao': 'Excesso de respingos na região soldada',
                    'cor_exibicao': '#17a2b8'
                },
                {
                    'nome': 'Desalinhamento',
                    'descricao': 'Peças não estão alinhadas corretamente',
                    'cor_exibicao': '#6f42c1'
                },
                {
                    'nome': 'Sobreposição Incorreta',
                    'descricao': 'Cordões de solda sobrepostos inadequadamente',
                    'cor_exibicao': '#e83e8c'
                }
            ]
            
            for defeito_data in tipos_defeito:
                defeito, created = TipoDefeito.objects.get_or_create(
                    nome=defeito_data['nome'],
                    defaults=defeito_data
                )
                if created:
                    self.stdout.write(f'  ✅ Criado: {defeito.nome}')
                else:
                    self.stdout.write(f'  ⚠️  Já existe: {defeito.nome}')
            
            # 5. USUÁRIOS DE EXEMPLO (se não existirem)
            self.stdout.write('👥 Criando usuários de exemplo...')
            
            # Usuário admin
            admin_user, created = Usuario.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@empresa.com',
                    'nome_completo': 'Administrador do Sistema',
                    'tipo_usuario': 'admin',
                    'ativo': True
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write('  ✅ Criado usuário admin (senha: admin123)')
            
            # Usuário qualidade
            qual_user, created = Usuario.objects.get_or_create(
                username='qualidade',
                defaults={
                    'email': 'qualidade@empresa.com',
                    'nome_completo': 'Inspetor de Qualidade',
                    'tipo_usuario': 'qualidade',
                    'ativo': True
                }
            )
            if created:
                qual_user.set_password('qual123')
                qual_user.save()
                self.stdout.write('  ✅ Criado usuário qualidade (senha: qual123)')
            
            # Usuário manutenção
            manut_user, created = Usuario.objects.get_or_create(
                username='manutencao',
                defaults={
                    'email': 'manutencao@empresa.com',
                    'nome_completo': 'Técnico de Manutenção',
                    'tipo_usuario': 'manutencao',
                    'ativo': True
                }
            )
            if created:
                manut_user.set_password('manut123')
                manut_user.save()
                self.stdout.write('  ✅ Criado usuário manutenção (senha: manut123)')
            
            # 6. SOLDADORES DE EXEMPLO
            self.stdout.write('👷 Criando soldadores de exemplo...')
            soldadores_exemplo = [
                {
                    'username': 'alcionei.soldador',
                    'nome_completo': 'Alcionei Santos',
                    'senha_simplificada': '1234'
                },
                {
                    'username': 'joao.soldador',
                    'nome_completo': 'João Silva',
                    'senha_simplificada': '5678'
                },
                {
                    'username': 'maria.soldadora',
                    'nome_completo': 'Maria Oliveira',
                    'senha_simplificada': '9101'
                }
            ]
            
            for sold_data in soldadores_exemplo:
                # Criar usuário
                usuario, created = Usuario.objects.get_or_create(
                    username=sold_data['username'],
                    defaults={
                        'email': f"{sold_data['username']}@empresa.com",
                        'nome_completo': sold_data['nome_completo'],
                        'tipo_usuario': 'soldador',
                        'ativo': True
                    }
                )
                if created:
                    usuario.set_password('soldador123')
                    usuario.save()
                
                # Criar soldador
                soldador, created = Soldador.objects.get_or_create(
                    usuario=usuario,
                    defaults={
                        'senha_simplificada': sold_data['senha_simplificada'],
                        'ativo': True
                    }
                )
                if created:
                    self.stdout.write(f'  ✅ Criado soldador: {soldador.usuario.nome_completo} (senha: {sold_data["senha_simplificada"]})')
                else:
                    self.stdout.write(f'  ⚠️  Já existe: {soldador.usuario.nome_completo}')
            
            # 7. MÓDULOS DE EXEMPLO
            self.stdout.write('🏗️ Criando módulos de exemplo...')
            modulos_exemplo = [
                {'nome': 'Módulo A', 'descricao': 'Módulo de produção A', 'ordem_exibicao': 1},
                {'nome': 'Módulo T', 'descricao': 'Módulo de produção T', 'ordem_exibicao': 2},
                {'nome': 'Módulo B', 'descricao': 'Módulo de produção B', 'ordem_exibicao': 3},
                {'nome': 'Módulo C', 'descricao': 'Módulo de produção C', 'ordem_exibicao': 4}
            ]
            
            for mod_data in modulos_exemplo:
                modulo, created = Modulo.objects.get_or_create(
                    nome=mod_data['nome'],
                    defaults=mod_data
                )
                if created:
                    self.stdout.write(f'  ✅ Criado: {modulo.nome}')
                else:
                    self.stdout.write(f'  ⚠️  Já existe: {modulo.nome}')
            
            # 8. COMPONENTES DE EXEMPLO
            self.stdout.write('🔩 Criando componentes de exemplo...')
            componentes_exemplo = [
                {
                    'nome': 'FAIS',
                    'descricao': 'Faixa de soldagem',
                    'tempo_padrao': 15.0,
                    'considera_diametro': True,
                    'formula_calculo': 'diametro * 0.02'
                },
                {
                    'nome': 'CHAPA DA CRUZETA',
                    'descricao': 'Soldagem da chapa da cruzeta',
                    'tempo_padrao': 25.0,
                    'considera_diametro': False
                },
                {
                    'nome': 'ATERRAMENTO',
                    'descricao': 'Soldagem do aterramento',
                    'tempo_padrao': 8.0,
                    'considera_diametro': False
                },
                {
                    'nome': 'ANTIGIRO',
                    'descricao': 'Soldagem do antigiro',
                    'tempo_padrao': 12.0,
                    'considera_diametro': False
                },
                {
                    'nome': 'BASE ISOLADORA',
                    'descricao': 'Soldagem da base isoladora',
                    'tempo_padrao': 18.0,
                    'considera_diametro': False
                }
            ]
            
            for comp_data in componentes_exemplo:
                componente, created = Componente.objects.get_or_create(
                    nome=comp_data['nome'],
                    defaults=comp_data
                )
                if created:
                    self.stdout.write(f'  ✅ Criado: {componente.nome}')
                else:
                    self.stdout.write(f'  ⚠️  Já existe: {componente.nome}')
            
            self.stdout.write(
                self.style.SUCCESS('🎉 Dados iniciais populados com sucesso!')
            )
            
            # Exibir resumo
            self.stdout.write('\n📊 RESUMO DOS DADOS CRIADOS:')
            self.stdout.write(f'  • Tipos de Parada Gerais: {TipoParada.objects.filter(categoria="geral").count()}')
            self.stdout.write(f'  • Tipos de Parada Manutenção: {TipoParada.objects.filter(categoria="manutencao").count()}')
            self.stdout.write(f'  • Tipos de Parada Qualidade: {TipoParada.objects.filter(categoria="qualidade").count()}')
            self.stdout.write(f'  • Tipos de Defeito: {TipoDefeito.objects.count()}')
            self.stdout.write(f'  • Usuários: {Usuario.objects.count()}')
            self.stdout.write(f'  • Soldadores: {Soldador.objects.count()}')
            self.stdout.write(f'  • Módulos: {Modulo.objects.count()}')
            self.stdout.write(f'  • Componentes: {Componente.objects.count()}')
            
            self.stdout.write('\n🔑 CREDENCIAIS DE ACESSO:')
            self.stdout.write('  👤 Admin: admin / admin123')
            self.stdout.write('  🔍 Qualidade: qualidade / qual123 (senha especial: qual123)')
            self.stdout.write('  🔧 Manutenção: manutencao / manut123 (senha especial: manut123)')
            self.stdout.write('  👷 Soldadores:')
            for soldador in Soldador.objects.all():
                self.stdout.write(f'     • {soldador.usuario.nome_completo}: {soldador.senha_simplificada}')
            
            self.stdout.write('\n✅ Sistema pronto para uso!')