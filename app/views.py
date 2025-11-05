# Importações necessárias do Django e outras bibliotecas
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout  
from django.contrib.auth.decorators import login_required  
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decouple import config
from django.core.mail import send_mail
from .models import CustomUser, Product, Solicitacao, Saidas, Entradas, logs

# ============================================================================
# FUNÇÕES GERAIS
# ============================================================================

def home(request):
    """View da página inicial do sistema"""
    if request.user.is_authenticated:
        auth_logout(request)
    return render(request, 'home.html')

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
    minhas_solicitacoes = Solicitacao.objects.filter(solicitante=request.user).order_by('-data_solicitacao')[:10]
    
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
# FUNÇÕES DE RELATÓRIOS
# ============================================================================

@login_required
def gerar_relatorio_pdf(request):
    """View para gerar relatório PDF do estoque - BLOQUEADA para usuário comum"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from datetime import datetime
    
    produtos = Product.objects.all().order_by('nome')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph("Relatório de Estoque Geral", styles['Title'])
    elements.append(title)
    
    date = Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
    elements.append(date)
    elements.append(Paragraph("<br/>", styles['Normal']))
    
    data = [['Código', 'Nome', 'Quantidade', 'Local']]
    
    for produto in produtos:
        data.append([
            produto.codigo,
            produto.nome,
            str(produto.quantidade),
            produto.local,
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    return response

@login_required
def logs(request):
    """View para exibir logs do sistema - APENAS SUPERADMIN"""
    if request.user.nivel_acesso != 'superadmin':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_super')
    
    from .models import logs as LogsModel
    logs_list = LogsModel.objects.all().order_by('-data_hora')[:200]
    
    context = {
        'logs': logs_list,
    }
    return render(request, 'logs.html', context)