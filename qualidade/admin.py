from django.contrib import admin
from .models import TipoDefeito, Defeito

@admin.register(TipoDefeito)
class TipoDefeitoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'cor_exibicao')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    list_editable = ('ativo',)

@admin.register(Defeito)
class DefeitoAdmin(admin.ModelAdmin):
    list_display = ('tipo_defeito', 'soldador', 'tamanho_mm', 'area_defeito', 
                   'data_deteccao', 'usuario_qualidade')
    list_filter = ('tipo_defeito', 'data_deteccao')
    search_fields = ('soldador__usuario__nome_completo', 'tipo_defeito__nome')
    readonly_fields = ('area_defeito',)
