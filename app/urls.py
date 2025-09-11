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
]