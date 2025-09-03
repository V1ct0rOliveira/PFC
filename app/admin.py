from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'nome', 'sobrenome', 'nivel_acesso', 'is_verified')
    list_filter = ('nivel_acesso', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'nome', 'sobrenome')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('nome', 'sobrenome', 'telefone', 'nivel_acesso', 'is_verified')
        }),
    )