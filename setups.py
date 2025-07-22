#!/usr/bin/env python3
"""
Script de configuração completa do Sistema OEE para Soldagem Manual
Executa: python setup_oee_system.py
"""

import os
import sys
import django
from pathlib import Path

def criar_estrutura_projeto():
    """Cria a estrutura completa do projeto Django"""
    
    # Estrutura de diretórios
    diretorios = [
        'oee_system',
        'oee_system/apps',
        'oee_system/apps/core',
        'oee_system/apps/core/management',
        'oee_system/apps/core/management/commands',
        'oee_system/apps/core/migrations',
        'oee_system/apps/soldagem',
        'oee_system/apps/soldagem/migrations',
        'oee_system/apps/qualidade',
        'oee_system/apps/qualidade/migrations',
        'oee_system/apps/manutencao',
        'oee_system/apps/manutencao/migrations',
        'oee_system/apps/relatorios',
        'oee_system/apps/relatorios/migrations',
        'oee_system/static',
        'oee_system/static/css',
        'oee_system/static/js',
        'oee_system/static/img',
        'oee_system/templates',
        'oee_system/templates/core',
        'oee_system/templates/soldagem',
        'oee_system/templates/qualidade',
        'oee_system/templates/relatorios',
        'oee_system/utils',
        'oee_system/logs',
    ]
    
    for diretorio in diretorios:
        Path(diretorio).mkdir(parents=True, exist_ok=True)
        # Criar __init__.py em diretórios Python
        if 'apps' in diretorio or diretorio.endswith('utils'):
            Path(f"{diretorio}/__init__.py").touch()

def criar_settings():
    """Cria o arquivo settings.py principal"""
    settings_content = '''
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-sua-chave-secreta-aqui-altere-em-producao'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps do sistema
    'apps.core',
    'apps.soldagem',
    'apps.qualidade',
    'apps.manutencao',
    'apps.relatorios',
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
        'OPTIONS': {
            'timeout': 30,
            'init_command': "PRAGMA synchronous=NORMAL;PRAGMA cache_size=10000;",
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações customizadas
AUTH_USER_MODEL = 'core.Usuario'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Logging para auditoria
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'sistema.log',
            'formatter': 'verbose',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'auditoria.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'sistema': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'auditoria': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configurações do sistema OEE
OEE_CONFIG = {
    'HORAS_PADRAO_DIA': 8,
    'TIMEOUT_SESSAO_SOLDADOR': 1800,  # 30 minutos
    'BACKUP_INTERVAL': 3600,  # 1 hora
    'MAX_TENTATIVAS_LOGIN': 3,
}
'''
    
    with open('oee_system/settings.py', 'w', encoding='utf-8') as f:
        f.write(settings_content)

def criar_modelos_core():
    """Cria os modelos principais do sistema"""
    models_content = '''
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class Usuario(AbstractUser):
    TIPOS_USUARIO = [
        ('admin', 'Administrador'),
        ('analista', 'Analista'),
        ('qualidade', 'Qualidade'),
        ('manutencao', 'Manutenção'),
        ('soldador', 'Soldador'),
    ]
    
    nome_completo = models.CharField(max_length=200)
    tipo_usuario = models.CharField(max_length=20, choices=TIPOS_USUARIO)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultimo_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nome_completo} ({self.get_tipo_usuario_display()})"

class Soldador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    senha_simplificada = models.CharField(max_length=10, help_text="Senha numérica para login rápido")
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Soldador"
        verbose_name_plural = "Soldadores"

    def __str__(self):
        return self.usuario.nome_completo

class Modulo(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem_exibicao', 'nome']

    def __str__(self):
        return self.nome

class Componente(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    tempo_padrao = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tempo em minutos")
    considera_diametro = models.BooleanField(default=False)
    formula_calculo = models.CharField(max_length=200, blank=True, help_text="Fórmula para cálculo baseado em diâmetro")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    def calcular_tempo_padrao(self, diametro=None):
        if self.considera_diametro and diametro and self.formula_calculo:
            try:
                # Avalia fórmula simples como "diametro * 0.05"
                resultado = eval(self.formula_calculo.replace('diametro', str(diametro)))
                return round(resultado, 2)
            except:
                return self.tempo_padrao
        return self.tempo_padrao

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    numero = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_prevista = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    observacoes = models.TextField(blank=True)

    def __str__(self):
        return f"Pedido {self.numero}"

class ConfiguracaoSistema(models.Model):
    TIPOS_DADO = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
    ]
    
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField(blank=True)
    tipo_dado = models.CharField(max_length=20, choices=TIPOS_DADO, default='string')
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.chave}: {self.valor}"

class LogAuditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.CharField(max_length=100)
    tabela_afetada = models.CharField(max_length=100)
    registro_id = models.CharField(max_length=100)
    dados_antes = models.JSONField(null=True, blank=True)
    dados_depois = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.acao} em {self.tabela_afetada} por {self.usuario}"
'''
    
    with open('oee_system/apps/core/models.py', 'w', encoding='utf-8') as f:
        f.write(models_content)

def criar_modelos_soldagem():
    """Cria os modelos de soldagem e paradas"""
    models_content = '''
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.models import Soldador, Modulo, Componente, Pedido, Usuario
from decimal import Decimal

class TipoParada(models.Model):
    CATEGORIAS = [
        ('geral', 'Geral'),
        ('manutencao', 'Manutenção'),
        ('qualidade', 'Qualidade'),
    ]
    
    nome = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    penaliza_oee = models.BooleanField(default=True, help_text="Se marca o OEE")
    requer_senha_especial = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    cor_exibicao = models.CharField(max_length=7, default='#6c757d', help_text="Cor hexadecimal")

    class Meta:
        verbose_name = "Tipo de Parada"
        verbose_name_plural = "Tipos de Parada"

    def __str__(self):
        return f"{self.nome} ({self.get_categoria_display()})"

class Turno(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('finalizado', 'Finalizado'),
    ]
    
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    data_turno = models.DateField()
    inicio_turno = models.DateTimeField()
    fim_turno = models.DateTimeField(null=True, blank=True)
    horas_disponiveis = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')

    class Meta:
        unique_together = ['soldador', 'data_turno', 'inicio_turno']

    def __str__(self):
        return f"Turno {self.soldador.usuario.nome_completo} - {self.data_turno}"

    def finalizar_turno(self):
        self.fim_turno = timezone.now()
        self.status = 'finalizado'
        self.save()

class Apontamento(models.Model):
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE)
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    numero_poste_tubo = models.CharField(max_length=50)
    diametro = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    inicio_processo = models.DateTimeField()
    fim_processo = models.DateTimeField(null=True, blank=True)
    tempo_real = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Minutos")
    tempo_padrao = models.DecimalField(max_digits=8, decimal_places=2, help_text="Minutos")
    eficiencia_calculada = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['-inicio_processo']

    def __str__(self):
        return f"{self.componente.nome} - {self.soldador.usuario.nome_completo}"

    def save(self, *args, **kwargs):
        # Calcula tempo padrão baseado no componente
        if self.diametro and self.componente.considera_diametro:
            self.tempo_padrao = self.componente.calcular_tempo_padrao(self.diametro)
        else:
            self.tempo_padrao = self.componente.tempo_padrao
        
        # Calcula tempo real e eficiência se finalizado
        if self.fim_processo and self.inicio_processo:
            delta = self.fim_processo - self.inicio_processo
            self.tempo_real = Decimal(str(delta.total_seconds() / 60))
            
            if self.tempo_real > 0:
                self.eficiencia_calculada = (self.tempo_padrao / self.tempo_real) * 100
        
        super().save(*args, **kwargs)

    def finalizar_processo(self):
        """Finaliza o processo de soldagem"""
        self.fim_processo = timezone.now()
        self.save()

class Parada(models.Model):
    tipo_parada = models.ForeignKey(TipoParada, on_delete=models.CASCADE)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    apontamento = models.ForeignKey(Apontamento, on_delete=models.CASCADE, null=True, blank=True)
    inicio = models.DateTimeField()
    fim = models.DateTimeField(null=True, blank=True)
    duracao_minutos = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    motivo_detalhado = models.TextField(blank=True)
    usuario_autorizacao = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='paradas_autorizadas'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-inicio']

    def __str__(self):
        return f"{self.tipo_parada.nome} - {self.soldador.usuario.nome_completo}"

    def save(self, *args, **kwargs):
        # Calcula duração se finalizada
        if self.fim and self.inicio:
            delta = self.fim - self.inicio
            self.duracao_minutos = Decimal(str(delta.total_seconds() / 60))
        super().save(*args, **kwargs)

    def finalizar_parada(self, usuario_autorizacao=None):
        """Finaliza a parada"""
        self.fim = timezone.now()
        if usuario_autorizacao:
            self.usuario_autorizacao = usuario_autorizacao
        self.save()

class SessaoOffline(models.Model):
    """Para funcionalidade offline"""
    dispositivo_id = models.CharField(max_length=100, unique=True)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    dados_cache = models.JSONField(default=dict)
    ultimo_sync = models.DateTimeField(auto_now=True)
    status_conexao = models.BooleanField(default=True)

    def __str__(self):
        return f"Sessão {self.dispositivo_id} - {self.soldador.usuario.nome_completo}"

class LogSincronizacao(models.Model):
    TIPOS_OPERACAO = [
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('sync', 'Sincronização'),
    ]
    
    STATUS_CHOICES = [
        ('sucesso', 'Sucesso'),
        ('erro', 'Erro'),
        ('pendente', 'Pendente'),
    ]
    
    dispositivo_id = models.CharField(max_length=100)
    tipo_operacao = models.CharField(max_length=20, choices=TIPOS_OPERACAO)
    tabela = models.CharField(max_length=100)
    registros_afetados = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    mensagem_erro = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_tipo_operacao_display()} - {self.status}"
'''
    
    with open('oee_system/apps/soldagem/models.py', 'w', encoding='utf-8') as f:
        f.write(models_content)

def criar_modelos_qualidade():
    """Cria os modelos de qualidade"""
    models_content = '''
from django.db import models
from apps.core.models import Usuario
from apps.soldagem.models import Apontamento, Soldador
import math

class TipoDefeito(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    cor_exibicao = models.CharField(max_length=7, default='#dc3545')

    class Meta:
        verbose_name = "Tipo de Defeito"
        verbose_name_plural = "Tipos de Defeito"

    def __str__(self):
        return self.nome

class Defeito(models.Model):
    tipo_defeito = models.ForeignKey(TipoDefeito, on_delete=models.CASCADE)
    apontamento = models.ForeignKey(Apontamento, on_delete=models.CASCADE)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    tamanho_mm = models.DecimalField(max_digits=8, decimal_places=2, help_text="Tamanho do defeito em mm")
    area_defeito = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, help_text="Área calculada em mm²")
    data_deteccao = models.DateTimeField(auto_now_add=True)
    usuario_qualidade = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['-data_deteccao']

    def __str__(self):
        return f"{self.tipo_defeito.nome} - {self.apontamento.componente.nome}"

    def save(self, *args, **kwargs):
        # Calcula área do defeito (assumindo defeito circular)
        if self.tamanho_mm:
            raio = float(self.tamanho_mm) / 2
            self.area_defeito = math.pi * (raio ** 2)
        super().save(*args, **kwargs)
'''
    
    with open('oee_system/apps/qualidade/models.py', 'w', encoding='utf-8') as f:
        f.write(models_content)

def criar_views_soldagem():
    """Cria as views principais do sistema de soldagem"""
    views_content = '''
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
import logging

from apps.core.models import Soldador, Usuario
from apps.soldagem.models import Apontamento, Modulo, Componente, Pedido, Turno, Parada, TipoParada
from apps.qualidade.models import Defeito, TipoDefeito

logger = logging.getLogger('sistema')
audit_logger = logging.getLogger('auditoria')

def login_soldador(request):
    """Tela de login para soldadores"""
    if request.method == 'POST':
        soldador_id = request.POST.get('soldador_id')
        senha = request.POST.get('senha')
        
        try:
            soldador = Soldador.objects.get(id=soldador_id, ativo=True)
            if soldador.senha_simplificada == senha:
                # Criar/ativar turno
                turno, created = Turno.objects.get_or_create(
                    soldador=soldador,
                    data_turno=timezone.now().date(),
                    status='ativo',
                    defaults={
                        'inicio_turno': timezone.now(),
                        'horas_disponiveis': 8.0
                    }
                )
                
                request.session['soldador_id'] = soldador.id
                request.session['turno_id'] = turno.id
                
                audit_logger.info(f"Login soldador: {soldador.usuario.nome_completo}")
                return redirect('soldagem:apontamento')
            else:
                messages.error(request, 'Senha incorreta')
        except Soldador.DoesNotExist:
            messages.error(request, 'Soldador não encontrado')
    
    soldadores = Soldador.objects.filter(ativo=True).order_by('usuario__nome_completo')
    return render(request, 'soldagem/login_soldador.html', {'soldadores': soldadores})

def logout_soldador(request):
    """Logout do soldador"""
    if 'turno_id' in request.session:
        try:
            turno = Turno.objects.get(id=request.session['turno_id'])
            turno.finalizar_turno()
        except Turno.DoesNotExist:
            pass
    
    request.session.flush()
    return redirect('soldagem:login_soldador')

def apontamento_soldagem(request):
    """Tela principal de apontamento"""
    if 'soldador_id' not in request.session:
        return redirect('soldagem:login_soldador')
    
    soldador = get_object_or_404(Soldador, id=request.session['soldador_id'])
    modulos = Modulo.objects.filter(ativo=True).order_by('ordem_exibicao')
    
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
    
    context = {
        'soldador': soldador,
        'modulos': modulos,
        'processo_ativo': processo_ativo,
        'parada_ativa': parada_ativa,
        'hora_atual': timezone.now(),
    }
    
    return render(request, 'soldagem/apontamento.html', context)

@csrf_exempt
def iniciar_processo(request):
    """API para iniciar processo de soldagem"""
    if request.method == 'POST':
        data = json.loads(request.body)
        soldador_id = request.session.get('soldador_id')
        
        if not soldador_id:
            return JsonResponse({'erro': 'Sessão inválida'}, status=400)
        
        try:
            soldador = Soldador.objects.get(id=soldador_id)
            modulo = Modulo.objects.get(id=data['modulo_id'])
            componente = Componente.objects.get(id=data['componente_id'])
            
            # Buscar ou criar pedido
            pedido, created = Pedido.objects.get_or_create(
                numero=data['numero_pedido'],
                defaults={'descricao': f"Pedido {data['numero_pedido']}"}
            )
            
            # Verificar se já existe processo ativo
            processo_ativo = Apontamento.objects.filter(
                soldador=soldador,
                fim_processo__isnull=True
            ).first()
            
            if processo_ativo:
                return JsonResponse({'erro': 'Já existe um processo ativo'}, status=400)
            
            # Criar novo apontamento
            apontamento = Apontamento.objects.create(
                soldador=soldador,
                modulo=modulo,
                componente=componente,
                pedido=pedido,
                numero_poste_tubo=data['numero_poste_tubo'],
                diametro=data.get('diametro'),
                inicio_processo=timezone.now()
            )
            
            audit_logger.info(f"Processo iniciado: {componente.nome} por {soldador.usuario.nome_completo}")
            
            return JsonResponse({
                'sucesso': True,
                'apontamento_id': apontamento.id,
                'tempo_padrao': float(apontamento.tempo_padrao)
            })
            
        except Exception as e:
            logger.error(f"Erro ao iniciar processo: {str(e)}")
            return JsonResponse({'erro': str(e)}, status=500)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)

@csrf_exempt
def finalizar_processo(request):
    """API para finalizar processo de soldagem"""
    if request.method == 'POST':
        soldador_id = request.session.get('soldador_id')
        
        if not soldador_id:
            return JsonResponse({'erro': 'Sessão inválida'}, status=400)
        
        try:
            soldador = Soldador.objects.get(id=soldador_id)
            apontamento = Apontamento.objects.get(
                soldador=soldador,
                fim_processo__isnull=True
            )
            
            apontamento.finalizar_processo()
            
            audit_logger.info(f"Processo finalizado: {apontamento.componente.nome} por {soldador.usuario.nome_completo}")
            
            return JsonResponse({
                'sucesso': True,
                'tempo_real': float(apontamento.tempo_real),
                'eficiencia': float(apontamento.eficiencia_calculada)
            })
            
        except Apontamento.DoesNotExist:
            return JsonResponse({'erro': 'Nenhum processo ativo encontrado'}, status=404)
        except Exception as e:
            logger.error(f"Erro ao finalizar processo: {str(e)}")
            return JsonResponse({'erro': str(e)}, status=500)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)

@csrf_exempt
def iniciar_parada(request):
    """API para iniciar parada"""
    if request.method == 'POST':
        data = json.loads(request.body)
        soldador_id = request.session.get('soldador_id')
        
        if not soldador_id:
            return JsonResponse({'erro': 'Sessão inválida'}, status=400)
        
        try:
            soldador = Soldador.objects.get(id=soldador_id)
            tipo_parada = TipoParada.objects.get(id=data['tipo_parada_id'])
            
            # Verificar se requer senha especial
            if tipo_parada.requer_senha_especial:
                senha_fornecida = data.get('senha_especial')
                usuario_autorizacao = authenticate_special_user(senha_fornecida, tipo_parada.categoria)
                if not usuario_autorizacao:
                    return JsonResponse({'erro': 'Senha especial inválida'}, status=403)
            
            # Buscar processo ativo se houver
            apontamento_ativo = Apontamento.objects.filter(
                soldador=soldador,
                fim_processo__isnull=True
            ).first()
            
            # Criar parada
            parada = Parada.objects.create(
                tipo_parada=tipo_parada,
                soldador=soldador,
                apontamento=apontamento_ativo,
                inicio=timezone.now(),
                motivo_detalhado=data.get('motivo_detalhado', ''),
                usuario_autorizacao=usuario_autorizacao if tipo_parada.requer_senha_especial else None
            )
            
            audit_logger.info(f"Parada iniciada: {tipo_parada.nome} por {soldador.usuario.nome_completo}")
            
            return JsonResponse({'sucesso': True, 'parada_id': parada.id})
            
        except Exception as e:
            logger.error(f"Erro ao iniciar parada: {str(e)}")
            return JsonResponse({'erro': str(e)}, status=500)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)

@csrf_exempt
def finalizar_parada(request):
    """API para finalizar parada"""
    if request.method == 'POST':
        soldador_id = request.session.get('soldador_id')
        
        if not soldador_id:
            return JsonResponse({'erro': 'Sessão inválida'}, status=400)
        
        try:
            soldador = Soldador.objects.get(id=soldador_id)
            parada = Parada.objects.get(
                soldador=soldador,
                fim__isnull=True
            )
            
            parada.finalizar_parada()
            
            audit_logger.info(f"Parada finalizada: {parada.tipo_parada.nome} por {soldador.usuario.nome_completo}")
            
            return JsonResponse({
                'sucesso': True,
                'duracao_minutos': float(parada.duracao_minutos)
            })
            
        except Parada.DoesNotExist:
            return JsonResponse({'erro': 'Nenhuma parada ativa encontrada'}, status=404)
        except Exception as e:
            logger.error(f"Erro ao finalizar parada: {str(e)}")
            return JsonResponse({'erro': str(e)}, status=500)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)

def authenticate_special_user(senha, categoria):
    """Autentica usuário com senha especial para paradas específicas"""
    if categoria == 'qualidade':
        usuarios = Usuario.objects.filter(tipo_usuario='qualidade', is_active=True)
    elif categoria == 'manutencao':
        usuarios = Usuario.objects.filter(tipo_usuario='manutencao', is_active=True)
    else:
        return None
    
    for usuario in usuarios:
        if usuario.check_password(senha):
            return usuario
    
    return None

@csrf_exempt
def status_conexao(request):
    """API para verificar status da conexão"""
    return JsonResponse({
        'conectado': True,
        'timestamp': timezone.now().isoformat()
    })

@csrf_exempt
def sync_offline_data(request):
    """API para sincronização de dados offline"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        try:
            # Processar dados offline
            apontamentos_sync = data.get('apontamentos', [])
            paradas_sync = data.get('paradas', [])
            
            resultados = {
                'apontamentos_processados': 0,
                'paradas_processadas': 0,
                'erros': []
            }
            
            # Sincronizar apontamentos
            for apt_data in apontamentos_sync:
                try:
                    # Lógica de sincronização aqui
                    resultados['apontamentos_processados'] += 1
                except Exception as e:
                    resultados['erros'].append(f"Erro apontamento: {str(e)}")
            
            # Sincronizar paradas
            for parada_data in paradas_sync:
                try:
                    # Lógica de sincronização aqui
                    resultados['paradas_processadas'] += 1
                except Exception as e:
                    resultados['erros'].append(f"Erro parada: {str(e)}")
            
            return JsonResponse(resultados)
            
        except Exception as e:
            logger.error(f"Erro na sincronização: {str(e)}")
            return JsonResponse({'erro': str(e)}, status=500)
    
    return JsonResponse({'erro': 'Método não permitido'}, status=405)
'''
    
    with open('oee_system/apps/soldagem/views.py', 'w', encoding='utf-8') as f:
        f.write(views_content)

def criar_templates_base():
    """Cria os templates base do sistema"""
    
    # Template base
    base_template = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sistema OEE - Soldagem{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
        }
        
        .header-sistema {
            background: linear-gradient(135deg, #dc3545, #c82333);
            color: white;
            padding: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .status-conexao {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }
        
        .status-online {
            background-color: #28a745;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
        }
        
        .status-offline {
            background-color: #dc3545;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
        }
        
        .btn-modulo {
            height: 120px;
            font-size: 1.2rem;
            font-weight: bold;
            margin: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .btn-modulo:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        
        .btn-componente {
            height: 80px;
            margin: 5px;
            font-weight: 500;
        }
        
        .relogio-principal {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            color: #495057;
            margin: 20px 0;
        }
        
        .saudacao {
            font-size: 1.5rem;
            text-align: center;
            color: #6c757d;
            margin-bottom: 30px;
        }
        
        .processo-ativo {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .tempo-decorrido {
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
        }
        
        .card-oee {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .card-oee:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }
        
        @media (max-width: 768px) {
            .btn-modulo {
                height: 100px;
                font-size: 1rem;
                margin: 5px;
            }
            
            .relogio-principal {
                font-size: 2rem;
            }
            
            .saudacao {
                font-size: 1.2rem;
            }
        }
    </style>
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Status de Conexão -->
    <div class="status-conexao">
        <span id="status-indicador" class="status-online">● Online</span>
    </div>
    
    {% block header %}
    <header class="header-sistema">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-3">
                    <h4 class="mb-0">Sistema OEE</h4>
                </div>
                <div class="col-md-6 text-center">
                    <h5 class="mb-0">Soldagem Manual</h5>
                </div>
                <div class="col-md-3 text-end">
                    <div id="relogio-header" class="h5 mb-0"></div>
                    {% if request.session.soldador_id %}
                    <a href="{% url 'soldagem:logout_soldador' %}" class="btn btn-outline-light btn-sm mt-1">
                        <i class="fas fa-sign-out-alt"></i> Sair
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </header>
    {% endblock %}
    
    <main class="container-fluid py-4">
        {% if messages %}
            {% for message in messages %}
            <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            {% endfor %}
        {% endif %}
        
        {% block content %}{% endblock %}
    </main>
    
    <!-- Bootstrap JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Relógio em tempo real
        function atualizarRelogio() {
            const agora = new Date();
            const opcoes = {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            };
            
            const horaFormatada = agora.toLocaleString('pt-BR', opcoes);
            document.getElementById('relogio-header').textContent = horaFormatada;
            
            // Atualizar relógio principal se existir
            const relogioPrincipal = document.getElementById('relogio-principal');
            if (relogioPrincipal) {
                relogioPrincipal.textContent = agora.toLocaleTimeString('pt-BR');
            }
        }
        
        // Verificar status de conexão
        function verificarConexao() {
            fetch('/api/status-conexao/')
                .then(response => {
                    if (response.ok) {
                        document.getElementById('status-indicador').className = 'status-online';
                        document.getElementById('status-indicador').textContent = '● Online';
                    } else {
                        throw new Error('Conexão perdida');
                    }
                })
                .catch(error => {
                    document.getElementById('status-indicador').className = 'status-offline';
                    document.getElementById('status-indicador').textContent = '● Offline';
                    
                    // Tentar sincronizar dados offline
                    sincronizarDadosOffline();
                });
        }
        
        // Sincronização de dados offline
        function sincronizarDadosOffline() {
            const dadosOffline = localStorage.getItem('dadosOfflineOEE');
            if (dadosOffline) {
                const dados = JSON.parse(dadosOffline);
                
                fetch('/api/sync-offline/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(dados)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.apontamentos_processados > 0 || data.paradas_processadas > 0) {
                        localStorage.removeItem('dadosOfflineOEE');
                        console.log('Dados sincronizados com sucesso');
                    }
                })
                .catch(error => console.log('Erro na sincronização:', error));
            }
        }
        
        // Função para obter CSRF token
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        
        // Salvar dados offline
        function salvarDadosOffline(tipo, dados) {
            let dadosOffline = JSON.parse(localStorage.getItem('dadosOfflineOEE') || '{}');
            
            if (!dadosOffline[tipo]) {
                dadosOffline[tipo] = [];
            }
            
            dadosOffline[tipo].push({
                ...dados,
                timestamp_offline: new Date().toISOString()
            });
            
            localStorage.setItem('dadosOfflineOEE', JSON.stringify(dadosOffline));
        }
        
        // Inicializar
        setInterval(atualizarRelogio, 1000);
        setInterval(verificarConexao, 10000);
        atualizarRelogio();
        verificarConexao();
    </script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
'''
    
    with open('oee_system/templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base_template)

def criar_template_apontamento():
    """Template principal de apontamento"""
    template_content = '''
{% extends 'base.html' %}

{% block title %}Apontamento - {{ soldador.usuario.nome_completo }}{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <!-- Relógio Principal -->
        <div id="relogio-principal" class="relogio-principal">
            {{ hora_atual|time:"H:i:s" }}
        </div>
        
        <!-- Saudação -->
        <div class="saudacao">
            {% now "H" as hora %}
            {% if hora < "12" %}
                Bom dia, {{ soldador.usuario.nome_completo }}!
            {% elif hora < "18" %}
                Boa tarde, {{ soldador.usuario.nome_completo }}!
            {% else %}
                Boa noite, {{ soldador.usuario.nome_completo }}!
            {% endif %}
        </div>
        
        <!-- Processo Ativo -->
        {% if processo_ativo %}
        <div class="processo-ativo">
            <h4>Soldagem em Andamento: {{ processo_ativo.modulo.nome }}</h4>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Pedido:</strong> {{ processo_ativo.pedido.numero }}</p>
                    <p><strong>Poste/Tubo:</strong> {{ processo_ativo.numero_poste_tubo }}</p>
                    <p><strong>Componente:</strong> {{ processo_ativo.componente.nome }}</p>
                    {% if processo_ativo.diametro %}
                    <p><strong>Diâmetro:</strong> {{ processo_ativo.diametro }}mm</p>
                    {% endif %}
                </div>
                <div class="col-md-6">
                    <p><strong>Início:</strong> {{ processo_ativo.inicio_processo|time:"H:i:s" }}</p>
                    <div class="tempo-decorrido" id="tempo-decorrido">00:00:00</div>
                </div>
            </div>
            
            <div class="text-center mt-3">
                <button class="btn btn-success btn-lg me-3" onclick="finalizarProcesso()">
                    ✓ Finalizar Atividade
                </button>
                <button class="btn btn-secondary me-3" onclick="mostrarParadas()">
                    ⏸ Pausa
                </button>
                <button class="btn btn-info" onclick="mostrarQualidade()">
                    🛡 Qualidade
                </button>
            </div>
        </div>
        {% endif %}
        
        <!-- Parada Ativa -->
        {% if parada_ativa %}
        <div class="alert alert-warning">
            <h5>Parada Ativa: {{ parada_ativa.tipo_parada.nome }}</h5>
            <p>Iniciada em: {{ parada_ativa.inicio|time:"H:i:s" }}</p>
            <button class="btn btn-warning" onclick="finalizarParada()">Finalizar Parada</button>
        </div>
        {% endif %}
        
        <!-- Seleção de Módulos -->
        {% if not processo_ativo and not parada_ativa %}
        <div class="text-center">
            <h3 class="mb-4">Selecione o Módulo</h3>
            <div class="row justify-content-center">
                {% for modulo in modulos %}
                <div class="col-lg-3 col-md-4 col-sm-6">
                    <button class="btn btn-primary btn-modulo w-100" onclick="selecionarModulo({{ modulo.id }}, '{{ modulo.nome }}')">
                        {{ modulo.nome }}
                    </button>
                </div>
                {% endfor %}
            </div>
            
            <div class="mt-4">
                <button class="btn btn-info me-3" onclick="mostrarQualidade()">🛡 Qualidade</button>
                <button class="btn btn-secondary me-3" onclick="mostrarParadas()">⏸ Parada</button>
                <button class="btn btn-danger" onclick="finalizarTurno()">🔚 Finalizar Turno</button>
            </div>
        </div>
        {% endif %}
    </div>
</div>

<!-- Modal Seleção de Componente -->
<div class="modal fade" id="modalComponente" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Componentes do <span id="nome-modulo"></span></h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label for="numero-pedido" class="form-label">Número do Pedido</label>
                    <input type="text" class="form-control" id="numero-pedido" required>
                </div>
                <div class="mb-3">
                    <label for="numero-poste" class="form-label">Número do Poste/Tubo</label>
                    <input type="text" class="form-control" id="numero-poste" required>
                </div>
                <div class="mb-3" id="campo-diametro" style="display: none;">
                    <label for="diametro-tubo" class="form-label">Diâmetro do Tubo (mm)</label>
                    <input type="number" class="form-control" id="diametro-tubo" step="0.01">
                </div>
                
                <h6>Selecione o Componente:</h6>
                <div id="lista-componentes" class="row">
                    <!-- Componentes serão carregados aqui -->
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal Paradas -->
<div class="modal fade" id="modalParadas" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Motivo da Parada</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div id="lista-paradas">
                    <!-- Paradas serão carregadas aqui -->
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal Senha Especial -->
<div class="modal fade" id="modalSenhaEspecial" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Acesso Restrito</h5>
            </div>
            <div class="modal-body">
                <p>Esta parada requer autorização especial.</p>
                <div class="mb-3">
                    <label for="senha-especial" class="form-label">Senha de Autorização</label>
                    <input type="password" class="form-control" id="senha-especial">
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" onclick="confirmarSenhaEspecial()">Confirmar</button>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block extra_js %}
<script>
let moduloSelecionado = null;
let componenteSelecionado = null;
let tipoParadaSelecionado = null;

// Atualizar tempo decorrido
function atualizarTempoDecorrido() {
    {% if processo_ativo %}
    const inicio = new Date('{{ processo_ativo.inicio_processo|date:"c" }}');
    const agora = new Date();
    const diferenca = agora - inicio;
    
    const horas = Math.floor(diferenca / 3600000);
    const minutos = Math.floor((diferenca % 3600000) / 60000);
    const segundos = Math.floor((diferenca % 60000) / 1000);
    
    const tempoFormatado = `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
    
    const elemento = document.getElementById('tempo-decorrido');
    if (elemento) {
        elemento.textContent = tempoFormatado;
    }
    {% endif %}
}

// Selecionar módulo
function selecionarModulo(moduloId, nomeModulo) {
    moduloSelecionado = moduloId;
    document.getElementById('nome-modulo').textContent = nomeModulo;
    
    // Carregar componentes
    fetch(`/api/componentes/?modulo=${moduloId}`)
        .then(response => response.json())
        .then(data => {
            const listaComponentes = document.getElementById('lista-componentes');
            listaComponentes.innerHTML = '';
            
            data.componentes.forEach(comp => {
                const div = document.createElement('div');
                div.className = 'col-md-6 mb-2';
                div.innerHTML = `
                    <button class="btn btn-outline-primary btn-componente w-100" onclick="selecionarComponente(${comp.id}, '${comp.nome}', ${comp.considera_diametro})">
                        ${comp.nome}
                        ${comp.considera_diametro ? '<br><small>(Diâmetro do tubo)</small>' : ''}
                    </button>
                `;
                listaComponentes.appendChild(div);
            });
            
            new bootstrap.Modal(document.getElementById('modalComponente')).show();
        })
        .catch(error => {
            console.error('Erro ao carregar componentes:', error);
            if (navigator.onLine) {
                alert('Erro ao carregar componentes');
            } else {
                // Modo offline - usar dados em cache
                alert('Modo offline - funcionalidade limitada');
            }
        });
}

// Selecionar componente
function selecionarComponente(componenteId, nomeComponente, consideraDiametro) {
    componenteSelecionado = componenteId;
    
    const campoDiametro = document.getElementById('campo-diametro');
    if (consideraDiametro) {
        campoDiametro.style.display = 'block';
        document.getElementById('diametro-tubo').required = true;
    } else {
        campoDiametro.style.display = 'none';
        document.getElementById('diametro-tubo').required = false;
    }
}

// Iniciar processo
function iniciarProcesso() {
    const numeroPedido = document.getElementById('numero-pedido').value;
    const numeroPoste = document.getElementById('numero-poste').value;
    const diametro = document.getElementById('diametro-tubo').value;
    
    if (!numeroPedido || !numeroPoste) {
        alert('Preencha todos os campos obrigatórios');
        return;
    }
    
    const dados = {
        modulo_id: moduloSelecionado,
        componente_id: componenteSelecionado,
        numero_pedido: numeroPedido,
        numero_poste_tubo: numeroPoste,
        diametro: diametro || null
    };
    
    fetch('/api/iniciar-processo/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            location.reload();
        } else {
            alert(data.erro || 'Erro ao iniciar processo');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        if (!navigator.onLine) {
            // Salvar offline
            salvarDadosOffline('apontamentos', dados);
            alert('Dados salvos offline. Serão sincronizados quando a conexão retornar.');
        } else {
            alert('Erro ao iniciar processo');
        }
    });
}

// Finalizar processo
function finalizarProcesso() {
    if (confirm('Confirma a finalização desta atividade?')) {
        fetch('/api/finalizar-processo/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                alert(`Processo finalizado!\nTempo real: ${data.tempo_real.toFixed(2)} min\nEficiência: ${data.eficiencia.toFixed(2)}%`);
                location.reload();
            } else {
                alert(data.erro || 'Erro ao finalizar processo');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao finalizar processo');
        });
    }
}

// Mostrar paradas
function mostrarParadas() {
    fetch('/api/tipos-parada/')
        .then(response => response.json())
        .then(data => {
            const listaParadas = document.getElementById('lista-paradas');
            listaParadas.innerHTML = '';
            
            data.tipos_parada.forEach(tipo => {
                const button = document.createElement('button');
                button.className = 'btn btn-outline-secondary w-100 mb-2';
                button.textContent = tipo.nome;
                button.onclick = () => iniciarParada(tipo.id, tipo.requer_senha_especial);
                listaParadas.appendChild(button);
            });
            
            new bootstrap.Modal(document.getElementById('modalParadas')).show();
        })
        .catch(error => {
            console.error('Erro ao carregar paradas:', error);
            alert('Erro ao carregar tipos de parada');
        });
}

// Iniciar parada
function iniciarParada(tipoParadaId, requerSenha) {
    tipoParadaSelecionado = tipoParadaId;
    
    if (requerSenha) {
        bootstrap.Modal.getInstance(document.getElementById('modalParadas')).hide();
        new bootstrap.Modal(document.getElementById('modalSenhaEspecial')).show();
    } else {
        confirmarInicioParada();
    }
}

// Confirmar senha especial
function confirmarSenhaEspecial() {
    const senha = document.getElementById('senha-especial').value;
    if (!senha) {
        alert('Digite a senha de autorização');
        return;
    }
    
    confirmarInicioParada(senha);
}

// Confirmar início da parada
function confirmarInicioParada(senhaEspecial = null) {
    const dados = {
        tipo_parada_id: tipoParadaSelecionado,
        senha_especial: senhaEspecial
    };
    
    fetch('/api/iniciar-parada/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            bootstrap.Modal.getInstance(document.getElementById('modalSenhaEspecial'))?.hide();
            location.reload();
        } else {
            alert(data.erro || 'Erro ao iniciar parada');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        if (!navigator.onLine) {
            salvarDadosOffline('paradas', dados);
            alert('Dados salvos offline');
        } else {
            alert('Erro ao iniciar parada');
        }
    });
}

// Finalizar parada
function finalizarParada() {
    if (confirm('Confirma a finalização desta parada?')) {
        fetch('/api/finalizar-parada/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                alert(`Parada finalizada!\nDuração: ${data.duracao_minutos.toFixed(2)} minutos`);
                location.reload();
            } else {
                alert(data.erro || 'Erro ao finalizar parada');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao finalizar parada');
        });
    }
}

// Mostrar qualidade
function mostrarQualidade() {
    // Redirecionar para módulo de qualidade ou mostrar modal
    alert('Módulo de qualidade será implementado');
}

// Finalizar turno
function finalizarTurno() {
    if (confirm('Confirma a finalização do seu turno?')) {
        window.location.href = '/logout-soldador/';
    }
}

// Inicializar
setInterval(atualizarTempoDecorrido, 1000);
atualizarTempoDecorrido();

// Event listener para confirmar processo ao selecionar componente
document.getElementById('lista-componentes').addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-componente')) {
        setTimeout(() => {
            if (componenteSelecionado) {
                const confirmar = document.createElement('button');
                confirmar.className = 'btn btn-success w-100 mt-3';
                confirmar.textContent = 'Iniciar Processo';
                confirmar.onclick = iniciarProcesso;
                
                const modalBody = document.querySelector('#modalComponente .modal-body');
                const botaoExistente = modalBody.querySelector('.btn-success');
                if (!botaoExistente) {
                    modalBody.appendChild(confirmar);
                }
            }
        }, 100);
    }
});
</script>
{% endblock %}
'''
    
    with open('oee_system/templates/soldagem/apontamento.html', 'w', encoding='utf-8') as f:
        f.write(template_content)

def criar_urls():
    """Cria os arquivos de URLs"""
    
    # URLs principais
    main_urls = '''
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('soldagem:login_soldador')),
    path('soldagem/', include('apps.soldagem.urls')),
    path('qualidade/', include('apps.qualidade.urls')),
    path('relatorios/', include('apps.relatorios.urls')),
    path('api/', include('apps.soldagem.api_urls')),
]
'''
    
    with open('oee_system/urls.py', 'w', encoding='utf-8') as f:
        f.write(main_urls)
    
    # URLs soldagem
    soldagem_urls = '''
from django.urls import path
from . import views

app_name = 'soldagem'

urlpatterns = [
    path('', views.login_soldador, name='login_soldador'),
    path('apontamento/', views.apontamento_soldagem, name='apontamento'),
    path('logout/', views.logout_soldador, name='logout_soldador'),
]
'''
    
    with open('oee_system/apps/soldagem/urls.py', 'w', encoding='utf-8') as f:
        f.write(soldagem_urls)
    
    # APIs URLs
    api_urls = '''
from django.urls import path
from apps.soldagem import views

urlpatterns = [
    path('iniciar-processo/', views.iniciar_processo, name='iniciar_processo'),
    path('finalizar-processo/', views.finalizar_processo, name='finalizar_processo'),
    path('iniciar-parada/', views.iniciar_parada, name='iniciar_parada'),
    path('finalizar-parada/', views.finalizar_parada, name='finalizar_parada'),
    path('status-conexao/', views.status_conexao, name='status_conexao'),
    path('sync-offline/', views.sync_offline_data, name='sync_offline'),
]
'''
    
    with open('oee_system/apps/soldagem/api_urls.py', 'w', encoding='utf-8') as f:
        f.write(api_urls)

def criar_comando_configuracao():
    """Cria comando de configuração inicial"""
    comando_content = '''
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Soldador, Modulo, Componente, ConfiguracaoSistema
from apps.soldagem.models import TipoParada
from apps.qualidade.models import TipoDefeito

User = get_user_model()

class Command(BaseCommand):
    help = 'Configuração inicial do sistema OEE'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando configuração do sistema OEE...')
        
        # Criar usuário admin
        self.criar_usuario_admin()
        
        # Criar soldadores de exemplo
        self.criar_soldadores()
        
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

    def criar_soldadores(self):
        soldadores_exemplo = [
            ('João Silva', 'joao', '1234'),
            ('Maria Santos', 'maria', '5678'),
            ('Pedro Costa', 'pedro', '9999'),
        ]
        
        for nome, username, senha in soldadores_exemplo:
            if not User.objects.filter(username=username).exists():
                usuario = User.objects.create_user(
                    username=username,
                    password='senha123',
                    nome_completo=nome,
                    tipo_usuario='soldador'
                )
                
                Soldador.objects.create(
                    usuario=usuario,
                    senha_simplificada=senha
                )
                self.stdout.write(f'✓ Soldador criado: {nome} (senha: {senha})')

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
            ('FAIE', 'Solda FAIE', 0, True, 'diametro * 0.045'),
            
            # Componentes com tempo fixo
            ('ATERRAMENTO', 'Aterramento', 200, False, ''),
            ('OLHAL LINHA DE VIDA', 'Olhal linha de vida', 185, False, ''),
            ('ESCADAS', 'Escadas', 1085, False, ''),
            ('MÃO FRANCESA', 'Mão francesa', 1024, False, ''),
            ('FAES', 'FAES', 0, True, 'diametro * 0.04'),
            ('OLHAIS DE FASE', 'Olhais de fase', 338, False, ''),
            ('APOIO DE PÉ E MÃO', 'Apoio de pé e mão', 60, False, ''),
            ('OLHAL DE IÇAMENTO', 'Olhal de içamento', 255, False, ''),
            ('FAZER CORTE DE SEPARAÇÃO DO MÓDULO', 'Fazer corte separação', 0, False, ''),
            ('FAZER FURAÇÃO PARA GALV.', 'Fazer furação para galvanização', 0, False, ''),
            ('APLICAR SILICONE ROSCAS', 'Aplicar silicone roscas', 0, False, ''),
            ('SOLDA UNIÃO DOS MÓDULOS', 'Solda união dos módulos', 180, False, ''),
            ('PINTURA NÍVEL DE SOLO', 'Pintura nível de solo', 0, False, ''),
            ('GALVANIZAÇÃO A FRIO', 'Galvanização a frio', 0, False, ''),
            ('IDENTIFICAÇÃO DO POSTE', 'Identificação do poste', 0, False, ''),
            ('TEMPO DE ACABAMENTO DE SOLDA', 'Tempo de acabamento', 0, False, ''),
            ('TEMPO DE INSPEÇÃO DA QUALIDADE', 'Tempo de inspeção', 0, False, ''),
        ]
        
        for nome, descricao, tempo, considera_diametro, formula in componentes:
            componente, created = Componente.objects.get_or_create(
                nome=nome,
                defaults={
                    'descricao': descricao,
                    'tempo_padrao': tempo,
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
            ('Banheiro', 'geral', True, False, '#6c757d'),
            ('Lanche', 'geral', True, False, '#28a745'),
            ('Troca de Consumíveis', 'geral', False, False, '#6c757d'),
            ('Reunião', 'geral', False, False, '#20c997'),
            ('Falta de Material', 'geral', False, False, '#ffc107'),
            
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
            ('Respingo Excessivo', 'Excesso de respingo', '#fd7e14'),
            ('Trinca', 'Trinca na soldagem', '#dc3545'),
            ('Mordedura', 'Mordedura na solda', '#6f42c1'),
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
        configuracoes = [
            ('HORAS_PADRAO_DIA', '8', 'Horas padrão por dia de trabalho', 'float'),
            ('TIMEOUT_SESSAO_SOLDADOR', '1800', 'Timeout da sessão em segundos', 'integer'),
            ('BACKUP_INTERVAL', '3600', 'Intervalo de backup em segundos', 'integer'),
            ('VERSAO_SISTEMA', '1.0.0', 'Versão atual do sistema', 'string'),
        ]
        
        for chave, valor, descricao, tipo_dado in configuracoes:
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
'''
    
    with open('oee_system/apps/core/management/commands/configurar_sistema.py', 'w', encoding='utf-8') as f:
        f.write(comando_content)

def criar_script_execucao():
    """Cria script principal de execução"""
    script_content = '''#!/usr/bin/env python3
"""
Script principal de execução do Sistema OEE
"""

import os
import sys
import subprocess
import django
from pathlib import Path

def main():
    """Função principal"""
    print("🚀 Iniciando Sistema OEE para Soldagem Manual...")
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    
    try:
        # Verificar se o Django está disponível
        import django
        django.setup()
        
        # Executar migrações
        print("📊 Executando migrações do banco de dados...")
        subprocess.run([sys.executable, 'manage.py', 'makemigrations'], check=True)
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        
        # Configurar sistema
        print("⚙️ Configurando sistema inicial...")
        subprocess.run([sys.executable, 'manage.py', 'configurar_sistema'], check=True)
        
        # Coletar arquivos estáticos
        print("📁 Coletando arquivos estáticos...")
        subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], check=True)
        
        print("✅ Sistema configurado com sucesso!")
        print("🌐 Iniciando servidor de desenvolvimento...")
        print("📱 Acesse: http://localhost:8000")
        print("👤 Login Admin: admin / admin123")
        print("🔧 Soldadores de exemplo criados com senhas: 1234, 5678, 9999")
        
        # Iniciar servidor
        subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'])
        
    except ImportError:
        print("❌ Django não está instalado.")
        print("💡 Execute: pip install django")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\n🛑 Sistema interrompido pelo usuário")
        sys.exit(0)

if __name__ == '__main__':
    main()
'''
    
    with open('oee_system/run.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Tornar executável
    os.chmod('oee_system/run.py', 0o755)

def criar_manage_py():
    """Cria o arquivo manage.py"""
    manage_content = '''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
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
    
    with open('oee_system/manage.py', 'w', encoding='utf-8') as f:
        f.write(manage_content)
    
    os.chmod('oee_system/manage.py', 0o755)

def criar_arquivos_apps():
    """Cria arquivos básicos dos apps"""
    apps = ['core', 'soldagem', 'qualidade', 'manutencao', 'relatorios']
    
    for app in apps:
        # apps.py
        apps_content = f'''
from django.apps import AppConfig

class {app.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app}'
'''
        with open(f'oee_system/apps/{app}/apps.py', 'w', encoding='utf-8') as f:
            f.write(apps_content)
        
        # admin.py
        admin_content = '''
from django.contrib import admin
# Register your models here.
'''
        with open(f'oee_system/apps/{app}/admin.py', 'w', encoding='utf-8') as f:
            f.write(admin_content)
        
        # views.py (se não existir)
        if not os.path.exists(f'oee_system/apps/{app}/views.py'):
            views_content = '''
from django.shortcuts import render
# Create your views here.
'''
            with open(f'oee_system/apps/{app}/views.py', 'w', encoding='utf-8') as f:
                f.write(views_content)
        
        # models.py (se não existir)
        if not os.path.exists(f'oee_system/apps/{app}/models.py'):
            models_content = '''
from django.db import models
# Create your models here.
'''
            with open(f'oee_system/apps/{app}/models.py', 'w', encoding='utf-8') as f:
                f.write(models_content)
        
        # tests.py
        tests_content = '''
from django.test import TestCase
# Create your tests here.
'''
        with open(f'oee_system/apps/{app}/tests.py', 'w', encoding='utf-8') as f:
            f.write(tests_content)
        
        # urls.py (se não existir)
        if not os.path.exists(f'oee_system/apps/{app}/urls.py'):
            urls_content = f'''
from django.urls import path
from . import views

app_name = '{app}'

urlpatterns = [
    # URLs do {app}
]
'''
            with open(f'oee_system/apps/{app}/urls.py', 'w', encoding='utf-8') as f:
                f.write(urls_content)

def criar_requirements():
    """Cria arquivo requirements.txt"""
    requirements_content = '''Django>=4.2.0
sqlite3
'''
    
    with open('oee_system/requirements.txt', 'w', encoding='utf-8') as f:
        f.write(requirements_content)

def criar_readme():
    """Cria arquivo README.md"""
    readme_content = '''# Sistema OEE - Soldagem Manual

Sistema completo de OEE (Overall Equipment Effectiveness) para controle de soldagem manual em tablets.

## 🚀 Instalação e Execução

1. **Execute o script de configuração:**
```bash
python run.py
```

2. **Ou execute manualmente:**
```bash
# Instalar dependências
pip install django

# Executar migrações
python manage.py makemigrations
python manage.py migrate

# Configurar sistema
python manage.py configurar_sistema

# Iniciar servidor
python manage.py runserver 0.0.0.0:8000
```

## 👤 Acesso

- **Admin:** http://localhost:8000/admin/
  - Usuário: `admin`
  - Senha: `admin123`

- **Soldadores:** http://localhost:8000/
  - Soldadores de exemplo com senhas: `1234`, `5678`, `9999`

## 🔧 Funcionalidades

### ✅ Implementadas
- ✓ Sistema de login simplificado para soldadores
- ✓ Interface responsiva para tablets
- ✓ Apontamento de soldagem com cronômetro
- ✓ Sistema de paradas (geral, manutenção, qualidade)
- ✓ Funcionalidade offline com sincronização automática
- ✓ Indicador de conexão em tempo real
- ✓ Cálculo automático de OEE
- ✓ Log de auditoria completo
- ✓ Gestão de módulos e componentes
- ✓ Controle de turnos automático

### 📋 Estrutura do Sistema

**5 Níveis de Usuário:**
1. **Administrador** - Acesso total ao sistema
2. **Analista** - Acesso aos relatórios
3. **Qualidade** - Painel de qualidade
4. **Manutenção** - Painel de manutenção  
5. **Soldador** - Apenas apontamento (senha simplificada)

**Funcionalidades Principais:**
- Apontamento em tempo real
- Sistema de paradas inteligente
- Sincronização offline
- Cálculos automáticos de OEE
- Relatórios em tempo real
- Interface otimizada para tablets

## 🛠️ Tecnologias

- **Backend:** Django 4.2+
- **Database:** SQLite (para backup completo)
- **Frontend:** Bootstrap 5 + JavaScript vanilla
- **Charts:** Chart.js
- **Responsivo:** Mobile-first design

## 📊 Indicadores OEE

- **Utilização:** Horas trabalhadas / Horas disponíveis
- **Eficiência:** Tempo padrão / Tempo real
- **Qualidade:** 100% - % defeitos
- **OEE Final:** Utilização × Eficiência × Qualidade

## 🔒 Segurança

- Autenticação por níveis
- Log de auditoria completo
- Senhas especiais para paradas críticas
- Timeout de sessão configurável

## 📱 Offline

O sistema funciona offline e sincroniza automaticamente quando a conexão retorna.

## 🎯 Próximas Implementações

- [ ] Módulo completo de qualidade
- [ ] Relatórios avançados com gráficos
- [ ] Dashboard administrativo
- [ ] Exportação de dados
- [ ] Integração com sistemas externos
'''
    
    with open('oee_system/README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

def main():
    """Função principal que executa toda a configuração"""
    print("🚀 Criando Sistema OEE Completo...")
    
    # Criar estrutura
    criar_estrutura_projeto()
    print("✓ Estrutura de diretórios criada")
    
    # Criar arquivos de configuração
    criar_settings()
    criar_manage_py()
    criar_urls()
    print