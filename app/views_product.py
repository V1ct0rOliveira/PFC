from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth.decorators import login_required  
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decouple import config
from django.core.mail import send_mail, EmailMultiAlternatives
from .models import CustomUser, Product, Solicitacao, Movimentacao, Saidas, Entradas
from .views_log import registrar_log
from .whatsapp_service import WhatsAppService

# ============================================================================
# FUNÇÕES DE ESTOQUE - PRODUTOS
# ============================================================================

@login_required
def cadastro_produto(request):
    """View para cadastro de novos produtos no estoque - BLOQUEADA para usuário comum"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    if request.method == 'POST':
        nome = request.POST['nome']
        quantidade = int(request.POST['quantidade'])
        local = request.POST['local']
        codigo = request.POST['codigo']
        carencia = request.POST['carencia']
        
        if Product.objects.filter(codigo=codigo).exists():
            messages.error(request, 'Código do produto já existe')
            return render(request, 'cadastro_produto.html')
        
        produto = Product.objects.create(
            nome=nome,
            quantidade=quantidade,
            local=local,
            codigo=codigo,
            carencia=carencia
        )
        
        # Registrar log no banco
        registrar_log(
            acao="Produto cadastrado",
            usuario=request.user,
            detalhes=f"Cadastrou produto: {produto.nome} (Código: {produto.codigo})"
        )
        
        messages.success(request, 'Produto cadastrado com sucesso!')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    return render(request, 'cadastro_produto.html')

@login_required
def estoque_geral(request):
    """View para exibir o estoque geral de produtos"""
    produtos = Product.objects.all()
    
    codigo = request.GET.get('codigo', '').strip()
    nome = request.GET.get('nome', '').strip()
    
    if codigo:
        produtos = produtos.filter(codigo__icontains=codigo)
    if nome:
        produtos = produtos.filter(nome__icontains=nome)
    
    context = {
        'produtos': produtos,
        'filtros': {
            'codigo': codigo,
            'nome': nome,
        }
    }
    
    return render(request, 'estoque_geral.html', context)

@login_required
def deletar_produto(request, produto_id):
    """View para deletar produto - APENAS ADMIN/SUPERADMIN"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    produto = get_object_or_404(Product, id=produto_id)
    
    if request.method == 'POST':
        nome_produto = produto.nome
        codigo_produto = produto.codigo
        
        # Registrar log antes de deletar
        registrar_log(
            acao="Produto deletado",
            usuario=request.user,
            detalhes=f"Deletou produto: {nome_produto} (Código: {codigo_produto})"
        )
        
        produto.delete()
        
        messages.success(request, f'Produto {nome_produto} deletado com sucesso!')
        return redirect('estoque_geral')
    
    return redirect('estoque_geral')

@login_required
def editar_produto(request, produto_id):
    """View para editar produto - APENAS ADMIN/SUPERADMIN"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    produto = get_object_or_404(Product, id=produto_id)
    
    if request.method == 'POST':
        nome_antigo = produto.nome
        produto.nome = request.POST.get('nome', produto.nome)
        produto.local = request.POST.get('local', produto.local)
        produto.carencia = int(request.POST.get('carencia', produto.carencia))
        produto.save()
        
        # Registrar log
        registrar_log(
            acao="Produto editado",
            usuario=request.user,
            detalhes=f"Editou produto: {nome_antigo} -> {produto.nome} (Código: {produto.codigo})"
        )
        
        messages.success(request, f'Produto {produto.nome} editado com sucesso!')
        if request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    if request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

# ============================================================================
# FUNÇÕES DE ESTOQUE - MOVIMENTAÇÕES
# ============================================================================

@login_required
def listar_movimentacoes(request):
    """View para listar movimentações com filtros - BLOQUEADA para usuário comum"""
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    from django.core.paginator import Paginator
    
    movimentacoes = Movimentacao.objects.select_related('produto').order_by('-data_hora')
    
    codigo = request.GET.get('codigo', '').strip()
    usuario = request.GET.get('usuario', '').strip()
    data_inicio = request.GET.get('data_inicio', '').strip()
    data_fim = request.GET.get('data_fim', '').strip()
    
    if codigo:
        movimentacoes = movimentacoes.filter(produto__codigo__icontains=codigo)
    if usuario:
        movimentacoes = movimentacoes.filter(usuario__icontains=usuario)
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_hora__date__gte=data_inicio)
    if data_fim:
        movimentacoes = movimentacoes.filter(data_hora__date__lte=data_fim)
    
    paginator = Paginator(movimentacoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filtros': {
            'codigo': codigo,
            'usuario': usuario,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    
    return render(request, 'movimentacoes.html', context)

# ============================================================================
# FUNÇÕES DE ESTOQUE - SOLICITAÇÕES
# ============================================================================

@login_required
def solicitar_produto(request):
    """View para solicitar produtos"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        quantidade = int(request.POST.get('quantidade', 0))
        destino = request.POST.get('destino', '').strip()
        
        if quantidade <= 0:
            messages.error(request, 'Quantidade deve ser maior que zero')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        if not destino:
            messages.error(request, 'Campo destino é obrigatório')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        try:
            produto = Product.objects.get(codigo=codigo)
        except Product.DoesNotExist:
            messages.error(request, 'Produto não encontrado')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        solicitacao = Solicitacao.objects.create(
            produto=produto,
            quantidade=quantidade,
            destino=destino,
            solicitante=request.user.username,
        )
        
        Movimentacao.objects.create(
            tipo='SOLICITACAO',
            produto=produto,
            quantidade=quantidade,
            usuario=request.user.username,
            referencia_id=solicitacao.id,
            observacao=f'Solicitação #{solicitacao.id} criada - Destino: {destino}'
        )
        
        # Enviar notificações apenas para administradores (não superadmin)
        admins = CustomUser.objects.filter(nivel_acesso='admin')
        emails_admins = [admin.email for admin in admins if admin.email]
        
        # Enviar email
        if emails_admins:
            try:
                html_content = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                        .content {{ padding: 30px; }}
                        .info-box {{ background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0; }}
                        .footer {{ background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }}
                        .btn {{ display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🔔 Nova Solicitação de Produto</h1>
                            <p>Stock Flow - Sistema de Gerenciamento de Estoque</p>
                        </div>
                        <div class="content">
                            <h2>Solicitação #{solicitacao.id}</h2>
                            <p>Uma nova solicitação foi criada e precisa de sua validação:</p>
                            
                            <div class="info-box">
                                <p><strong>👤 Solicitante:</strong> {request.user.username}</p>
                                <p><strong>📦 Produto:</strong> {produto.nome}</p>
                                <p><strong>🏷️ Código:</strong> {produto.codigo}</p>
                                <p><strong>📊 Quantidade:</strong> {quantidade} unidades</p>
                                <p><strong>📍 Destino:</strong> {destino}</p>
                                <p><strong>📅 Data:</strong> {timezone.localtime(solicitacao.data_solicitacao).strftime('%d/%m/%Y às %H:%M')}</p>
                            </div>
                            
                            <p>Por favor, acesse o sistema para aprovar ou reprovar esta solicitação.</p>
                        </div>
                        <div class="footer">
                            <p>Este é um email automático. Não responda a esta mensagem.</p>
                            <p>Stock Flow &copy; 2025 - Sistema de Gerenciamento de Estoque</p>
                        </div>
                    </div>
                </body>
                </html>
                '''
                
                text_content = f'''Nova Solicitação de Produto - Stock Flow

Solicitação #{solicitacao.id}
Solicitante: {request.user.username}
Produto: {produto.nome} (Código: {produto.codigo})
Quantidade: {quantidade}
Destino: {destino}
Data: {timezone.localtime(solicitacao.data_solicitacao).strftime('%d/%m/%Y %H:%M')}

Por favor, acesse o sistema para aprovar ou reprovar esta solicitação.'''
                
                msg = EmailMultiAlternatives(
                    'Nova Solicitação de Produto - Stock Flow',
                    text_content,
                    config('EMAIL_HOST_USER'),
                    emails_admins
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=True)
            except Exception:
                pass
        
        # Enviar WhatsApp para administradores
        whatsapp = WhatsAppService()
        for admin in admins:
            if admin.telefone:
                dados_whatsapp = {
                    'id': solicitacao.id,
                    'solicitante': request.user.username,
                    'produto': produto.nome,
                    'codigo': produto.codigo,
                    'quantidade': quantidade,
                    'destino': destino,
                    'data': timezone.localtime(solicitacao.data_solicitacao).strftime('%d/%m/%Y às %H:%M')
                }
                whatsapp.send_notification(admin.telefone, 'nova_solicitacao', dados_whatsapp)
        
        # Registrar log no banco
        registrar_log(
            acao="Solicitação criada",
            usuario=request.user,
            detalhes=f"Solicitou {quantidade} unidades do produto: {produto.nome} - Destino: {destino}"
        )
        
        messages.success(request, f'Solicitação #{solicitacao.id} criada com sucesso!')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

@login_required
def aprovar_solicitacao(request, solicitacao_id):
    """View para aprovar solicitação e executar retirada automaticamente"""
    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id, status='PENDENTE')
    produto = solicitacao.produto
    
    if produto.quantidade < solicitacao.quantidade:
        messages.error(request, f'Estoque insuficiente para aprovação. Disponível: {produto.quantidade}, Solicitado: {solicitacao.quantidade}')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    with transaction.atomic():
        solicitacao.status = 'ATENDIDA'
        solicitacao.aprovador = request.user.username
        solicitacao.data_aprovacao = timezone.now()
        solicitacao.save()
        
        produto.quantidade -= solicitacao.quantidade
        produto.save()
        
        Saidas.objects.create(
            produto=produto,
            quantidade=solicitacao.quantidade,
            destino=solicitacao.destino,
            usuario=request.user.username,
        )
        
        Movimentacao.objects.create(
            tipo='RETIRADA',
            produto=produto,
            quantidade=solicitacao.quantidade,
            usuario=request.user.username,
            referencia_id=solicitacao.id,
            observacao=f'Solicitação #{solicitacao.id} aprovada e retirada executada automaticamente - Destino: {solicitacao.destino}'
        )
        
        # Enviar notificações de aprovação
        email = "beltramevictor13@gmail.com"
        
        # Enviar email
        try:
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .info-box {{ background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
                    .footer {{ background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Solicitação Aprovada</h1>
                        <p>Stock Flow - Sistema de Gerenciamento de Estoque</p>
                    </div>
                    <div class="content">
                        <h2>Solicitação #{solicitacao.id} Aprovada</h2>
                        <p>Uma solicitação foi aprovada e o produto foi retirado do estoque:</p>
                        
                        <div class="info-box">
                            <p><strong>👤 Solicitante:</strong> {solicitacao.solicitante}</p>
                            <p><strong>👨‍💼 Aprovador:</strong> {request.user.username}</p>
                            <p><strong>📦 Produto:</strong> {produto.nome}</p>
                            <p><strong>🏷️ Código:</strong> {produto.codigo}</p>
                            <p><strong>📊 Quantidade:</strong> -{solicitacao.quantidade} unidades</p>
                            <p><strong>📍 Destino:</strong> {solicitacao.destino}</p>
                            <p><strong>📅 Data Aprovação:</strong> {timezone.localtime().strftime('%d/%m/%Y às %H:%M')}</p>
                        </div>
                    </div>
                    <div class="footer">
                        <p>Este é um email automático. Não responda a esta mensagem.</p>
                        <p>Stock Flow &copy; 2025 - Sistema de Gerenciamento de Estoque</p>
                    </div>
                </div>
            </body>
            </html>
            '''
            
            text_content = f'Solicitação Aprovada - A solicitação #{solicitacao.id} foi aprovada por {request.user.username}. Produto: {produto.nome}, Quantidade: {solicitacao.quantidade}, Destino: {solicitacao.destino}.'
            
            msg = EmailMultiAlternatives(
                'Solicitação Aprovada - Stock Flow',
                text_content,
                config('EMAIL_HOST_USER'),
                [email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)
        except Exception:
            pass
        
        # Enviar WhatsApp para o solicitante
        try:
            solicitante_user = CustomUser.objects.get(username=solicitacao.solicitante)
            if solicitante_user.telefone:
                whatsapp = WhatsAppService()
                dados_whatsapp = {
                    'id': solicitacao.id,
                    'solicitante': solicitacao.solicitante,
                    'aprovador': request.user.username,
                    'produto': produto.nome,
                    'quantidade': solicitacao.quantidade,
                    'destino': solicitacao.destino,
                    'data_aprovacao': timezone.localtime().strftime('%d/%m/%Y às %H:%M')
                }
                whatsapp.send_notification(solicitante_user.telefone, 'solicitacao_aprovada', dados_whatsapp)
        except CustomUser.DoesNotExist:
            pass
        
        # Registrar log no banco
        registrar_log(
            acao="Solicitação aprovada",
            usuario=request.user.username,
            detalhes=f"Aprovou solicitação #{solicitacao.id} - {solicitacao.quantidade} unidades do produto: {produto.nome}"
        )
    
    messages.success(request, f'Solicitação #{solicitacao.id} aprovada e retirada executada automaticamente!')
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

@login_required
def reprovar_solicitacao(request, solicitacao_id):
    """View para reprovar solicitação"""
    solicitacao = get_object_or_404(Solicitacao, id=solicitacao_id, status='PENDENTE')
    produto = solicitacao.produto
    
    solicitacao.status = 'REPROVADA'
    solicitacao.aprovador = request.user.username
    solicitacao.data_aprovacao = timezone.now()
    solicitacao.save()
    
    # Enviar WhatsApp para o solicitante
    try:
        solicitante_user = CustomUser.objects.get(username=solicitacao.solicitante)
        if solicitante_user.telefone:
            whatsapp = WhatsAppService()
            dados_whatsapp = {
                'id': solicitacao.id,
                'solicitante': solicitacao.solicitante,
                'reprovador': request.user.username,
                'produto': produto.nome,
                'quantidade': solicitacao.quantidade,
                'destino': solicitacao.destino,
                'data_reprovacao': timezone.localtime().strftime('%d/%m/%Y às %H:%M')
            }
            whatsapp.send_notification(solicitante_user.telefone, 'solicitacao_reprovada', dados_whatsapp)
    except CustomUser.DoesNotExist:
        pass
    
    # Registrar log no banco
    registrar_log(
        acao="Solicitação reprovada",
        usuario=request.user.username,
        detalhes=f"Reprovou solicitação #{solicitacao.id} - {solicitacao.quantidade} unidades do produto: {solicitacao.produto.nome}"
    )
    
    messages.success(request, f'Solicitação #{solicitacao.id} reprovada!')
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')

# ============================================================================
# FUNÇÕES DE ESTOQUE - ENTRADAS E SAÍDAS
# ============================================================================

@login_required
def entrada_produto(request):
    """View para entrada de produtos"""
    if request.method == 'POST':
        email = "beltramevictor13@gmail.com"
        codigo = request.POST.get('codigo')
        quantidade = int(request.POST.get('quantidade', 0))
        
        if quantidade <= 0:
            messages.error(request, 'Quantidade deve ser maior que zero')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        try:
            produto = Product.objects.get(codigo=codigo)
        except Product.DoesNotExist:
            messages.error(request, 'Produto não encontrado')
            if request.user.nivel_acesso == 'comum':
                return redirect('dashboard_comum')
            elif request.user.nivel_acesso == 'admin':
                return redirect('dashboard_admin')
            else:
                return redirect('dashboard_super')
        
        with transaction.atomic():
            produto.quantidade += quantidade
            produto.save()
            
            Movimentacao.objects.create(
                tipo='ENTRADA',
                produto=produto,
                quantidade=quantidade,
                usuario=request.user.username,
                observacao=f'Entrada de {quantidade} unidades'
            )

            Entradas.objects.create(
                produto=produto,
                quantidade=quantidade,
                usuario=request.user.username,
            )

            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .info-box {{ background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
                    .footer {{ background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⬆️ Entrada de Produto</h1>
                        <p>Stock Flow - Sistema de Gerenciamento de Estoque</p>
                    </div>
                    <div class="content">
                        <h2>Nova Entrada Registrada</h2>
                        <p>Uma entrada de produto foi registrada no sistema:</p>
                        
                        <div class="info-box">
                            <p><strong>👤 Usuário:</strong> {request.user.username}</p>
                            <p><strong>📦 Produto:</strong> {produto.nome}</p>
                            <p><strong>🏷️ Código:</strong> {produto.codigo}</p>
                            <p><strong>📊 Quantidade:</strong> +{quantidade} unidades</p>
                            <p><strong>📅 Data:</strong> {timezone.localtime().strftime('%d/%m/%Y às %H:%M')}</p>
                        </div>
                    </div>
                    <div class="footer">
                        <p>Este é um email automático. Não responda a esta mensagem.</p>
                        <p>Stock Flow &copy; 2025 - Sistema de Gerenciamento de Estoque</p>
                    </div>
                </div>
            </body>
            </html>
            '''
            
            text_content = f'Entrada de Produto - O usuário {request.user.username} realizou a entrada de {quantidade} unidades do produto {produto.nome}.'
            
            msg = EmailMultiAlternatives(
                'Entrada de Produto - Stock Flow',
                text_content,
                config('EMAIL_HOST_USER'),
                [email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)
            
            # Enviar WhatsApp apenas para administradores
            admins = CustomUser.objects.filter(nivel_acesso='admin')
            whatsapp = WhatsAppService()
            for admin in admins:
                if admin.telefone:
                    dados_whatsapp = {
                        'produto': produto.nome,
                        'codigo': produto.codigo,
                        'quantidade': quantidade,
                        'usuario': request.user.username,
                        'data': timezone.localtime().strftime('%d/%m/%Y às %H:%M')
                    }
                    whatsapp.send_notification(admin.telefone, 'entrada_produto', dados_whatsapp)
            
            # Registrar log no banco
            registrar_log(
                acao="Entrada de produto",
                usuario=request.user.username,
                detalhes=f"Registrou entrada de {quantidade} unidades do produto: {produto.nome}"
            )
        
        messages.success(request, f'Entrada de {quantidade} unidades de {produto.nome} registrada!')
        if request.user.nivel_acesso == 'comum':
            return redirect('dashboard_comum')
        elif request.user.nivel_acesso == 'admin':
            return redirect('dashboard_admin')
        else:
            return redirect('dashboard_super')
    
    if request.user.nivel_acesso == 'comum':
        return redirect('dashboard_comum')
    elif request.user.nivel_acesso == 'admin':
        return redirect('dashboard_admin')
    else:
        return redirect('dashboard_super')