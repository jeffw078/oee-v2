from django.utils import timezone
# core/models.py
from django.db import models

# Por enquanto o core não tem modelos específicos
# Todos os modelos estão sendo centralizados no app soldagem
# para simplificar a implementação inicial

# Este arquivo pode ser expandido futuramente com:
# - Configurações gerais do sistema
# - Modelos de cache de relatórios
# - Configurações de empresa
# - Etc.

class ConfiguracaoGlobal(models.Model):
    """Configurações globais do sistema"""
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração Global"
        verbose_name_plural = "Configurações Globais"

    def __str__(self):
        return f"{self.chave}: {self.valor}"