from django.contrib import admin
from .models import Pedido, Turno, Apontamento, TipoParada, Parada

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'status', 'data_criacao', 'data_prevista')
    list_filter = ('status', 'data_criacao')
    search_fields = ('numero', 'descricao')
    list_editable = ('status',)

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('soldador', 'data_turno', 'inicio_turno', 'fim_turno', 'status', 'horas_disponiveis')
    list_filter = ('status', 'data_turno')
    search_fields = ('soldador__usuario__nome_completo',)

@admin.register(Apontamento)
class ApontamentoAdmin(admin.ModelAdmin):
    list_display = ('soldador', 'componente', 'pedido', 'numero_poste_tubo', 
                   'inicio_processo', 'fim_processo', 'tempo_real', 'eficiencia_calculada')
    list_filter = ('modulo', 'componente', 'inicio_processo')
    search_fields = ('soldador__usuario__nome_completo', 'pedido__numero', 'numero_poste_tubo')
    readonly_fields = ('tempo_real', 'eficiencia_calculada')

@admin.register(TipoParada)
class TipoParadaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'penaliza_oee', 'requer_senha_especial', 'ativo')
    list_filter = ('categoria', 'penaliza_oee', 'requer_senha_especial', 'ativo')
    search_fields = ('nome',)
    list_editable = ('ativo',)

@admin.register(Parada)
class ParadaAdmin(admin.ModelAdmin):
    list_display = ('soldador', 'tipo_parada', 'inicio', 'fim', 'duracao_minutos')
    list_filter = ('tipo_parada__categoria', 'inicio')
    search_fields = ('soldador__usuario__nome_completo', 'tipo_parada__nome')
    readonly_fields = ('duracao_minutos',)
