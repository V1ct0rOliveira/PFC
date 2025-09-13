from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login, name='login'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),
    path('cadastro_produto/', views.cadastro_produto, name='cadastro_produto'), 
    path('estoque_geral/', views.estoque_geral, name='estoque_geral'),
    path('gerar_relatorio_pdf/', views.gerar_relatorio_pdf, name='gerar_relatorio_pdf'),
    
    # URLs do sistema de estoque
    path('solicitar-produto/', views.solicitar_produto, name='solicitar_produto'),
    path('aprovar-solicitacao/<int:solicitacao_id>/', views.aprovar_solicitacao, name='aprovar_solicitacao'),
    path('reprovar-solicitacao/<int:solicitacao_id>/', views.reprovar_solicitacao, name='reprovar_solicitacao'),
    path('entrada-produto/', views.entrada_produto, name='entrada_produto'),
    path('retirada-direta/', views.retirada_direta, name='retirada_direta'),
    path('movimentacoes/', views.listar_movimentacoes, name='listar_movimentacoes'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
]