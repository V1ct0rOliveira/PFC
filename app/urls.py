# Importações necessárias do Django
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # URLs de autenticação e perfil do usuário
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login, name='login'),
    path('perfil/', views.perfil, name='perfil'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),
    path('esqueci_senha/', views.esqueci_senha, name='esqueci_senha'),
    path('verificar_token/', views.verificar_token, name='verificar_token'),
    path('nova_senha/', views.nova_senha, name='nova_senha'),

    # URLs de geração de relatórios
    path('gerar_relatorio_pdf/', views.gerar_relatorio_pdf, name='gerar_relatorio_pdf'),
    
    # URLs de controle dos produtos
    path('cadastro_produto/', views.cadastro_produto, name='cadastro_produto'), 
    path('estoque_geral/', views.estoque_geral, name='estoque_geral'),
    path('solicitar-produto/', views.solicitar_produto, name='solicitar_produto'),
    path('aprovar-solicitacao/<int:solicitacao_id>/', views.aprovar_solicitacao, name='aprovar_solicitacao'),
    path('reprovar-solicitacao/<int:solicitacao_id>/', views.reprovar_solicitacao, name='reprovar_solicitacao'),
    path('entrada-produto/', views.entrada_produto, name='entrada_produto'),
    path('retirada-direta/', views.retirada_direta, name='retirada_direta'),
    path('movimentacoes/', views.listar_movimentacoes, name='listar_movimentacoes'),
]