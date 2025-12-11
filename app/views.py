from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout  
from django.contrib.auth.decorators import login_required  
from django.contrib import messages
from decouple import config
from .models import CustomUser, Product, Solicitacao, Saidas, Entradas, logs

# ============================================================================
# FUNÇÕES GERAIS
# ============================================================================

def home(request):
    """View da página inicial do sistema"""
    if request.user.is_authenticated:
        auth_logout(request)
    return render(request, 'home.html')

def termos_politicas(request):
    """View para exibir termos de uso e políticas de privacidade"""
    return render(request, 'termos_politicas.html')

# ============================================================================
# FUNÇÕES DE DASHBOARD
# ============================================================================

@login_required
def dashboard(request):
    """Redireciona para dashboard específico baseado no nível de acesso"""
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    elif request.user.nivel_acesso == 'superadmin':
        return redirect('dashboard_super')

@login_required
def dashboard_comum(request):
    """Dashboard para usuários comuns"""
    produtos = Product.objects.all()
    minhas_solicitacoes = Solicitacao.objects.filter(solicitante=request.user.username).order_by('-data_solicitacao')[:10]
    
    context = {
        'produtos': produtos,
        'minhas_solicitacoes': minhas_solicitacoes,
    }
    return render(request, 'dashboard_comum.html', context)

@login_required
def dashboard_admin(request):
    """Dashboard para administradores"""
    if request.user.nivel_acesso not in ['admin', 'superadmin']:
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    produtos = Product.objects.all()
    solicitacoes_pendentes = Solicitacao.objects.filter(status='PENDENTE').order_by('-data_solicitacao')
    entradas_recentes = Entradas.objects.select_related('produto').order_by('-data_entrada')[:50]
    saidas_recentes = Saidas.objects.select_related('produto').order_by('-data_saida')[:50]
    
    context = {
        'produtos': produtos,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'entradas_recentes': entradas_recentes,
        'saidas_recentes': saidas_recentes,
    }
    return render(request, 'dashboard_admin.html', context)

@login_required
def dashboard_super(request):
    """Dashboard para superadministradores"""
    if request.user.nivel_acesso != 'superadmin':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    produtos = Product.objects.all()
    solicitacoes_pendentes = Solicitacao.objects.filter(status='PENDENTE').order_by('-data_solicitacao')
    entradas_recentes = Entradas.objects.select_related('produto').order_by('-data_entrada')[:50]
    saidas_recentes = Saidas.objects.select_related('produto').order_by('-data_saida')[:50]
    usuarios = CustomUser.objects.all()
    
    context = {
        'produtos': produtos,
        'solicitacoes_pendentes': solicitacoes_pendentes,
        'entradas_recentes': entradas_recentes,
        'saidas_recentes': saidas_recentes,
        'usuarios': usuarios,
    }
    return render(request, 'dashboard_super.html', context)

# ============================================================================
# FUNÇÕES DE LOGS
# ============================================================================

@login_required
def logs(request):
    """View para exibir logs do sistema - APENAS SUPERADMIN"""
    if request.user.nivel_acesso != 'superadmin':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_super')
    
    from django.core.paginator import Paginator
    from .models import logs as LogsModel
    
    logs_list = LogsModel.objects.all().order_by('-data_hora')
    
    usuario = request.GET.get('usuario', '').strip()
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()
    
    if usuario:
        logs_list = logs_list.filter(usuario__icontains=usuario)
    if data_inicio:
        logs_list = logs_list.filter(data_hora__date__gte=data_inicio)
    if data_fim:
        logs_list = logs_list.filter(data_hora__date__lte=data_fim)
    
    paginator = Paginator(logs_list, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filtros': {
            'usuario': usuario,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    return render(request, 'logs.html', context)