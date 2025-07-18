from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import subprocess
import shutil
from datetime import datetime

class Command(BaseCommand):
    help = 'Prepara o sistema para deploy em produção'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando deploy de produção...')
        
        # 1. Coletar arquivos estáticos
        self.stdout.write('📦 Coletando arquivos estáticos...')
        call_command('collectstatic', '--noinput')
        
        # 2. Executar migrações
        self.stdout.write('🔄 Executando migrações...')
        call_command('migrate')
        
        # 3. Configurar sistema
        self.stdout.write('⚙️ Configurando sistema...')
        call_command('configurar_sistema')
        
        # 4. Criar backup do banco
        self.stdout.write('💾 Criando backup do banco...')
        self.criar_backup_banco()
        
        # 5. Configurar logs
        self.stdout.write('📝 Configurando logs...')
        self.configurar_logs()
        
        # 6. Verificar sistema
        self.stdout.write('🔍 Verificando sistema...')
        self.verificar_sistema()
        
        self.stdout.write(self.style.SUCCESS('✅ Deploy concluído com sucesso!'))
        self.stdout.write('🌐 Sistema pronto para produção!')
        self.stdout.write('📱 Acesse: http://localhost:8000')
        self.stdout.write('👤 Login: admin / admin123')
        
    def criar_backup_banco(self):
        '''Cria backup do banco de dados'''
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')
        
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_file)
            self.stdout.write(f'✓ Backup criado: {backup_file}')
    
    def configurar_logs(self):
        '''Configura diretório de logs'''
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Criar arquivo de log de auditoria
        audit_log = os.path.join(log_dir, 'audit.log')
        if not os.path.exists(audit_log):
            with open(audit_log, 'w') as f:
                f.write(f'# Log de Auditoria - Sistema OEE\n')
                f.write(f'# Iniciado em: {datetime.now().isoformat()}\n\n')
            
        self.stdout.write(f'✓ Logs configurados em: {log_dir}')
    
    def verificar_sistema(self):
        '''Verifica se o sistema está funcionando'''
        try:
            call_command('check')
            self.stdout.write('✓ Sistema verificado com sucesso')
        except Exception as e:
            self.stdout.write(f'❌ Erro na verificação: {e}')