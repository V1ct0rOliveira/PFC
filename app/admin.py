from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import Product, Entradas, Saidas, Solicitacao, Movimentacao, logs

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'nivel_acesso', 'is_verified')
    list_filter = ('nivel_acesso', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('nome', 'sobrenome', 'telefone', 'nivel_acesso', 'is_verified')
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade', 'local', 'codigo', 'carencia')
    search_fields = ('nome', 'codigo')

    fieldsets = (
        ('Detalhes do Produto', {
            'fields': ('nome', 'quantidade', 'local', 'codigo', 'carencia')
        }),
    )

@admin.register(Entradas)
class EntradasAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade', 'data_entrada', 'usuario')
    search_fields = ('produto__nome', 'usuario__username', 'data_entrada')

    fieldsets = (
        ('Detalhes da Entrada', {
            'fields': ('produto', 'quantidade', 'usuario')
        }),
    )

@admin.register(Saidas)
class SaidasAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade', 'destino', 'data_saida', 'usuario')
    search_fields = ('produto__nome', 'usuario__username', 'data_saida')

    fieldsets = (
        ('Detalhes da Saída', {
            'fields': ('produto', 'quantidade', 'destino', 'usuario')
        }),
    )

@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade', 'destino', 'status', 'data_solicitacao')
    search_fields = ('produto__nome', 'destino', 'status', 'data_solicitacao')

    fieldsets = (
        ('Detalhes da Solicitação', {
            'fields': ('produto', 'quantidade', 'usuario', 'status')
        }),
    )

@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'produto', 'quantidade', 'usuario', 'data_hora')
    search_fields = ('tipo', 'produto__nome', 'usuario__username', 'data_hora')

    fieldsets = (
        ('Detalhes da Movimentação', {
            'fields': ('tipo', 'produto', 'quantidade', 'usuario')
        }),
    )

@admin.register(logs)
class LogsAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'acao', 'data_hora')
    search_fields = ('usuario__username', 'acao', 'data_hora')

    fieldsets = (
        ('Detalhes do Log', {
            'fields': ('usuario', 'acao')
        }),
    )