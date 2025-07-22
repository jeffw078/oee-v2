# core/models.py - ESTRUTURA CORRETA

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Usuario(AbstractUser):
    """
    Modelo de usuário customizado
    IMPORTANTE: senha_simplificada NÃO deve estar aqui!
    """
    TIPOS_USUARIO = [
        ('admin', 'Administrador'),
        ('analista', 'Analista'),
        ('qualidade', 'Qualidade'),
        ('manutencao', 'Manutenção'),
        ('soldador', 'Soldador'),
    ]
    
    email = models.EmailField(unique=True)
    nome_completo = models.CharField(max_length=200)
    tipo_usuario = models.CharField(max_length=20, choices=TIPOS_USUARIO)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    ultimo_login = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nome_completo', 'tipo_usuario']
    
    class Meta:
        ordering = ['nome_completo']
    
    def __str__(self):
        return self.nome_completo

class Soldador(models.Model):
    """
    Modelo específico para soldadores
    AQUI SIM deve ter senha_simplificada!
    """
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    senha_simplificada = models.CharField(max_length=10, help_text="Senha numérica simples para login rápido")
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['usuario__nome_completo']
    
    def __str__(self):
        return self.usuario.nome_completo

class Modulo(models.Model):
    """Módulos de produção"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['ordem_exibicao', 'nome']
    
    def __str__(self):
        return self.nome

class Componente(models.Model):
    """Componentes que podem ser soldados"""
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    tempo_padrao = models.DecimalField(max_digits=10, decimal_places=2)
    considera_diametro = models.BooleanField(default=False)
    formula_calculo = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class ConfiguracaoSistema(models.Model):
    """Configurações gerais do sistema"""
    TIPOS_DADO = [
        ('string', 'Texto'),
        ('integer', 'Número Inteiro'),
        ('float', 'Número Decimal'),
        ('boolean', 'Verdadeiro/Falso'),
    ]
    
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField(blank=True)
    tipo_dado = models.CharField(max_length=20, choices=TIPOS_DADO, default='string')
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['chave']
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'
    
    def __str__(self):
        return f"{self.chave}: {self.valor}"

class LogAuditoria(models.Model):
    """Log de auditoria para rastreamento de ações"""
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.CharField(max_length=100)
    tabela_afetada = models.CharField(max_length=100)
    registro_id = models.IntegerField(null=True, blank=True)
    dados_antes = models.JSONField(null=True, blank=True)
    dados_depois = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
    
    def __str__(self):
        usuario_nome = self.usuario.nome_completo if self.usuario else 'Sistema'
        return f"{usuario_nome} - {self.acao} - {self.timestamp}"