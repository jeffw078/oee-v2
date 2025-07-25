#!/usr/bin/env python3
"""
Script final para resolver todos os problemas do Sistema OEE
Execute: python resolver_tudo.py
"""

import os
import sys
import shutil
import subprocess

def limpar_tudo():
    """Remove arquivos problemáticos"""
    print("🧹 Limpando arquivos problemáticos...")
    
    # Remover __pycache__
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs[:]:
            if dir_name == '__pycache__':
                shutil.rmtree(os.path.join(root, dir_name))
                dirs.remove(dir_name)
    
    # Remover .pyc
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
    
    # Remover banco de dados para começar do zero
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')
        print("✅ Banco de dados removido")
    
    if os.path.exists('oee_system.db'):
        os.remove('oee_system.db')
        print("✅ Banco OEE removido")
    
    print("✅ Limpeza concluída")

def criar_estrutura_completa():
    """Cria estrutura completa do projeto"""
    print("📁 Criando estrutura completa...")
    
    # Diretórios
    dirs = [
        'templates', 'templates/soldagem', 'templates/qualidade', 'templates/core',
        'static', 'static/css', 'static/js', 'logs', 'media'
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Apps
    apps = ['soldagem', 'qualidade', 'core']
    
    for app in apps:
        if os.path.exists(app):
            shutil.rmtree(app)
        
        os.makedirs(app, exist_ok=True)
        os.makedirs(f'{app}/migrations', exist_ok=True)
        
        # __init__.py
        with open(f'{app}/__init__.py', 'w') as f:
            f.write('')
        
        with open(f'{app}/migrations/__init__.py', 'w') as f:
            f.write('')
        
        # apps.py
        with open(f'{app}/apps.py', 'w') as f:
            f.write(f'''from django.apps import AppConfig

class {app.title()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app}'
    verbose_name = '{app.title()} do Sistema OEE'
''')
        
        # models.py básico
        with open(f'{app}/models.py', 'w') as f:
            f.write('from django.db import models\n\n# Models do {}\n'.format(app))
        
        # views.py básico
        with open(f'{app}/views.py', 'w') as f:
            f.write('from django.shortcuts import render\n\n# Views do {}\n'.format(app))
        
        # urls.py básico
        with open(f'{app}/urls.py', 'w') as f:
            f.write(f'''from django.urls import path
from . import views

app_name = '{app}'
urlpatterns = []
''')
        
        # admin.py básico
        with open(f'{app}/admin.py', 'w') as f:
            f.write('from django.contrib import admin\n\n# Admin do {}\n'.format(app))
        
        # tests.py
        with open(f'{app}/tests.py', 'w') as f:
            f.write('from django.test import TestCase\n\n# Tests do {}\n'.format(app))
        
        print(f"✅ App {app} criado")
    
    print("✅ Estrutura completa criada")

def configurar_django_basico():
    """Configura Django básico funcionando"""
    print("⚙️ Configurando Django básico...")
    
    # settings.py básico
    settings_content = '''import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = 'django-insecure-sistema-oee-secreto'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'soldagem',
    'qualidade',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

os.makedirs(BASE_DIR / 'logs', exist_ok=True)
'''
    
    with open('settings.py', 'w') as f:
        f.write(settings_content)
    
    # urls.py básico
    urls_content = '''from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Sistema OEE funcionando!</h1><p><a href='/admin/'>Admin</a></p>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('soldagem/', include('soldagem.urls')),
    path('qualidade/', include('qualidade.urls')),
    path('core/', include('core.urls')),
]
'''
    
    with open('urls.py', 'w') as f:
        f.write(urls_content)
    
    # manage.py
    manage_content = '''#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
'''
    
    with open('manage.py', 'w') as f:
        f.write(manage_content)
    
    print("✅ Configuração básica criada")

def testar_configuracao():
    """Testa se a configuração está funcionando"""
    print("🧪 Testando configuração...")
    
    try:
        # Testar check
        result = subprocess.run([sys.executable, 'manage.py', 'check'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Django check OK")
        else:
            print(f"❌ Django check falhou: {result.stderr}")
            return False
        
        # Fazer migração inicial
        subprocess.run([sys.executable, 'manage.py', 'migrate'], 
                      check=True, capture_output=True)
        print("✅ Migração inicial OK")
        
        # Criar superuser
        from django.core.management import execute_from_command_line
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
        
        import django
        django.setup()
        
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
            print("✅ Superuser criado: admin/admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    print("🚀 RESOLVER TODOS OS PROBLEMAS - SISTEMA OEE")
    print("=" * 50)
    
    # Verificar Python e Django
    try:
        import django
        print(f"✅ Django {django.get_version()} encontrado")
    except ImportError:
        print("📦 Instalando Django...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'django'], check=True)
        print("✅ Django instalado")
    
    etapas = [
        ("Limpando arquivos problemáticos", limpar_tudo),
        ("Criando estrutura completa", criar_estrutura_completa),
        ("Configurando Django básico", configurar_django_basico),
        ("Testando configuração", testar_configuracao),
    ]
    
    for nome, funcao in etapas:
        print(f"\n{nome}...")
        if not funcao():
            print(f"❌ Falha em: {nome}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 SISTEMA BASE FUNCIONANDO!")
    print("=" * 50)
    
    print("\n📋 STATUS:")
    print("✅ Django configurado")
    print("✅ Apps criados")
    print("✅ Banco de dados inicializado")
    print("✅ Admin criado: admin/admin123")
    
    print("\n📝 PRÓXIMOS PASSOS:")
    print("1. Substitua os arquivos pelos fornecidos no projeto OEE:")
    print("   - soldagem/models.py")
    print("   - soldagem/views.py")
    print("   - soldagem/urls.py")
    print("   - soldagem/admin.py")
    print("   - templates/soldagem/*.html")
    print("   - settings.py (atualizado)")
    print("   - urls.py (atualizado)")
    
    print("\n2. Execute as migrações:")
    print("   python manage.py makemigrations")
    print("   python manage.py migrate")
    
    print("\n3. Configure dados iniciais:")
    print("   python manage.py shell < configuracao_inicial.py")
    
    print("\n4. Inicie o servidor:")
    print("   python manage.py runserver 0.0.0.0:8000")
    
    # Testar servidor básico
    try:
        resposta = input("\n🧪 Testar servidor básico agora? (s/n): ")
        if resposta.lower() in ['s', 'sim']:
            print("\n🌐 Iniciando servidor básico...")
            print("📱 Acesse: http://localhost:8000/")
            print("👤 Admin: http://localhost:8000/admin/ (admin/admin123)")
            print("🛑 Use Ctrl+C para parar")
            subprocess.run([sys.executable, 'manage.py', 'runserver'])
    except KeyboardInterrupt:
        print("\n👋 Setup finalizado!")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelado pelo usuário")
        sys.exit(1)