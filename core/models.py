from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Usuario(AbstractUser):
    TIPOS_USUARIO = [
        ('admin', 'Administrador'),
        ('analista', 'Analista'),
        ('qualidade', 'Qualidade'),
        ('manutencao', 'Manutenção'),
        ('soldador', 'Soldador'),
    ]
    
    nome_completo = models.CharField(max_length=255)
    tipo_usuario = models.CharField(max_length=20, choices=TIPOS_USUARIO)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    ultimo_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nome_completo} ({self.get_tipo_usuario_display()})"

class Soldador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    senha_simplificada = models.CharField(max_length=10)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.usuario.nome_completo

class Modulo(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.IntegerField(default=1)
    data_criacao = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['ordem_exibicao']
    
    def __str__(self):
        return self.nome

class Componente(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    tempo_padrao = models.DecimalField(max_digits=10, decimal_places=2, help_text="Tempo em minutos")
    considera_diametro = models.BooleanField(default=False)
    formula_calculo = models.TextField(blank=True, help_text="Fórmula para cálculo baseado em diâmetro")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.nome

class ConfiguracaoSistema(models.Model):
    TIPOS_DADO = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
    ]
    
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField()
    tipo_dado = models.CharField(max_length=20, choices=TIPOS_DADO, default='string')
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.chave}: {self.valor}"

class LogAuditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=100)
    tabela_afetada = models.CharField(max_length=100)
    registro_id = models.CharField(max_length=100)
    dados_antes = models.JSONField(null=True, blank=True)
    dados_depois = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.usuario} - {self.acao} - {self.timestamp}"

class SessaoOffline(models.Model):
    dispositivo_id = models.CharField(max_length=100, unique=True)
    soldador = models.ForeignKey(Soldador, on_delete=models.CASCADE)
    dados_cache = models.JSONField(default=dict)
    ultimo_sync = models.DateTimeField(default=timezone.now)
    status_conexao = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.soldador} - {self.dispositivo_id}"