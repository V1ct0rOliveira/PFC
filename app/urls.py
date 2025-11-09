from django.urls import path
from . import views, views_api, views_users, views_product, views_reports

urlpatterns = [
    
    # URLs de dashboards
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard_comum/', views.dashboard_comum, name='dashboard_comum'),
    path('dashboard_admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard_super/', views.dashboard_super, name='dashboard_super'),
    path('logs/', views.logs, name='logs'),

    # URLs de termos de uso
    path('termos/', views.termos, name='termos'),

    # URLs de geração de relatórios
    path('relatorio_pdf_geral/', views_reports.relatorio_pdf_geral, name='relatorio_pdf_geral'),
    path('relatorio_excel_geral/', views_reports.relatorio_excel_geral, name='relatorio_excel_geral'),

    # URLs de autenticação e perfil do usuário
    path('cadastro/', views_users.cadastro, name='cadastro'),
    path('login/', views_users.login, name='login'),
    path('perfil/', views_users.perfil, name='perfil'),
    path('logout/', views_users.logout, name='logout'),
    path('esqueci_senha/', views_users.esqueci_senha, name='esqueci_senha'),
    path('verificar_token/', views_users.verificar_token, name='verificar_token'),
    path('nova_senha/', views_users.nova_senha, name='nova_senha'),
    path('setup_totp/', views_users.setup_totp, name='setup_totp'),
    path('verify_totp/', views_users.verify_totp, name='verify_totp'),
    path('reset_user_totp/<int:user_id>/', views_users.reset_user_totp, name='reset_user_totp'),
    path('tabela_usuarios/', views_users.tabela_usuarios, name='tabela_usuarios'),
    path('deletar_conta/', views_users.deletar_conta, name='deletar_conta'),

    # URLs de API
    path('api/listar_produtos/', views_api.listar_produtos_api, name='listar_produtos_api'),
    path('api/listar_produtos/<int:product_id>/', views_api.detalhes_produtos_api, name='detalhes_produtos_api'),
    path('api/listar_movimentacoes/', views_api.listar_movimentacoes_api, name='listar_movimentacoes_api'),
    path('api/listar_movimentacoes/<int:movimentacao_id>/', views_api.detalhes_movimentacoes_api, name='detalhes_movimentacoes_api'),
    
    # URLs de controle dos produtos
    path('cadastro_produto/', views_product.cadastro_produto, name='cadastro_produto'), 
    path('estoque_geral/', views_product.estoque_geral, name='estoque_geral'),
    path('solicitar-produto/', views_product.solicitar_produto, name='solicitar_produto'),
    path('aprovar-solicitacao/<int:solicitacao_id>/', views_product.aprovar_solicitacao, name='aprovar_solicitacao'),
    path('reprovar-solicitacao/<int:solicitacao_id>/', views_product.reprovar_solicitacao, name='reprovar_solicitacao'),
    path('entrada-produto/', views_product.entrada_produto, name='entrada_produto'),
    path('movimentacoes/', views_product.listar_movimentacoes, name='listar_movimentacoes'),
    path('deletar-produto/<int:produto_id>/', views_product.deletar_produto, name='deletar_produto'),
    path('editar-produto/<int:produto_id>/', views_product.editar_produto, name='editar_produto'),
]