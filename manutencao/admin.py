from django.contrib import admin
from soldagem.models import Parada, TipoParada

# Criar uma view customizada de paradas de manutenção
class ParadaManutencaoAdmin(admin.ModelAdmin):
    list_display = ('get_soldador_nome', 'tipo_parada', 'inicio', 'fim', 'duracao_minutos')
    list_filter = ('tipo_parada', 'data_criacao')
    search_fields = ('soldador__usuario__nome_completo', 'tipo_parada__nome')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tipo_parada__categoria='manutencao')
    
    def get_soldador_nome(self, obj):
        return obj.soldador.usuario.nome_completo
    get_soldador_nome.short_description = 'Soldador'

# Registrar proxy model se quiser separar no admin
class ParadaManutencaoProxy(Parada):
    class Meta:
        proxy = True
        verbose_name = 'Parada de Manutenção'
        verbose_name_plural = 'Paradas de Manutenção'

admin.site.register(ParadaManutencaoProxy, ParadaManutencaoAdmin)