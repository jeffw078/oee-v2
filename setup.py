#!/usr/bin/env python
"""
Script de setup automatizado para o Sistema OEE
Execute: python setup.py
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Executa comando e trata erros"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Concluído")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro em {description}:")
        print(f"   Comando: {command}")
        print(f"   Erro: {e.stderr}")
        return False

def create_directories():
    """Cria diretórios necessários"""
    print("\n📁 Criando diretórios necessários...")
    
    directories = [
        'logs',
        'backups', 
        'static',
        'media',
        'core/migrations',
        'soldagem/migrations',
        'qualidade/migrations',
        'manutencao/migrations',
        'relatorios/migrations'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {directory}")
    
    # Criar arquivos __init__.py nas migrations
    migration_dirs = [
        'core/migrations',
        'soldagem/migrations', 
        'qualidade/migrations',
        'manutencao/migrations',
        'relatorios/migrations'
    ]
    
    for migration_dir in migration_dirs:
        init_file = Path(migration_dir) / '__init__.py'
        if not init_file.exists():
            init_file.touch()
            print(f"   ✓ {migration_dir}/__init__.py")

def main():
    print("🚀 Configurando Sistema OEE...")
    print("=" * 50)
    
    # Verificar se está na pasta correta
    if not Path('manage.py').exists():
        print("❌ Erro: manage.py não encontrado!")
        print("   Execute este script na raiz do projeto Django")
        sys.exit(1)
    
    # 1. Criar diretórios
    create_directories()
    
    # 2. Instalar dependências
    success = run_command(
        "pip install -r requirements.txt",
        "Instalando dependências Python"
    )
    if not success:
        print("⚠️  Tentando com requeriments.txt...")
        run_command(
            "pip install -r requeriments.txt", 
            "Instalando dependências (arquivo com typo)"
        )
    
    # 3. Criar migrações
    apps = ['core', 'soldagem', 'qualidade', 'manutencao', 'relatorios']
    for app in apps:
        run_command(
            f"python manage.py makemigrations {app}",
            f"Criando migrações para {app}"
        )
    
    # 4. Executar migrações
    run_command(
        "python manage.py migrate",
        "Executando migrações do banco"
    )
    
    # 5. Configurar sistema
    run_command(
        "python manage.py configurar_sistema",
        "Configurando dados iniciais"
    )
    
    # 6. Coletar arquivos estáticos
    run_command(
        "python manage.py collectstatic --noinput",
        "Coletando arquivos estáticos"
    )
    
    print("\n" + "=" * 50)
    print("🎉 SISTEMA CONFIGURADO COM SUCESSO!")
    print("=" * 50)
    print("\n📋 INFORMAÇÕES IMPORTANTES:")
    print("👤 Usuário Admin: admin")
    print("🔑 Senha Admin: admin123")
    print("🌐 Para iniciar o servidor: python manage.py runserver")
    print("📱 Acesse: http://localhost:8000")
    print("\n💡 DICA: Use o comando 'python manage.py deploy_production' para deploy completo")

if __name__ == "__main__":
    main()