from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout  
from django.contrib.auth.decorators import login_required  
from django.contrib import messages
from django.utils import timezone
from decouple import config
from django.core.mail import send_mail
from .models import CustomUser
from .views_log import registrar_log
import re

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def validar_senha_forte(senha):
    """Valida se a senha atende aos critérios de segurança"""
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres"
    
    if not re.search(r'[A-Z]', senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', senha):
        return False, "A senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'\d', senha):
        return False, "A senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False, "A senha deve conter pelo menos um caractere especial (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Senha válida"

# ============================================================================
# FUNÇÕES DE AUTENTICAÇÃO E USUÁRIO
# ============================================================================

def cadastro(request):
    """View para cadastro de novos usuários - APENAS SUPERADMIN"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.nivel_acesso != 'superadmin':
        messages.error(request, 'Acesso negado. Apenas superadministradores podem cadastrar usuários.')
        return redirect('dashboard_super')
    
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        nome = request.POST['first_name']
        sobrenome = request.POST['last_name']
        nivel_acesso = request.POST['nivel_acesso']
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Usuário já existe')
            return render(request, 'cadastro.html')
        
        senha_valida, mensagem = validar_senha_forte(password)
        if not senha_valida:
            messages.error(request, mensagem)
            return render(request, 'cadastro.html')
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=nome,
            last_name=sobrenome,
            nivel_acesso=nivel_acesso
        )
        
        # Registrar log no banco
        registrar_log(
            acao="Usuário cadastrado",
            usuario=user,
            detalhes=f"Novo usuário cadastrado: {username} ({email})"
        )
        
        messages.success(request, 'Cadastro realizado com sucesso!')
        return redirect('dashboard_super')
    
    return render(request, 'cadastro.html')

def login(request):
    """View para autenticação de usuários"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.totp_enabled:
                request.session['setup_user_id'] = user.id
                return redirect('setup_totp')
            else:
                request.session['login_user_id'] = user.id
                return redirect('verify_totp')
        else:
            messages.error(request, 'Credenciais inválidas')
    
    return render(request, 'login.html')

def logout(request):
    """View para logout do usuário"""
    if request.user.is_authenticated:
        # Registrar log de logout no banco
        registrar_log(
            acao="Logout realizado",
            usuario=request.user,
            detalhes=f"Logout feito com sucesso pelo usuário {request.user.username} | IP: {request.META.get('REMOTE_ADDR')}"
        )
    
    auth_logout(request)
    return redirect('home')

@login_required
def perfil(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.telefone = request.POST.get('telefone', user.telefone)
        
        nova_senha = request.POST.get('nova_senha')
        if nova_senha:
            senha_valida, mensagem = validar_senha_forte(nova_senha)
            if not senha_valida:
                messages.error(request, mensagem)
                return render(request, 'perfil.html')
            user.set_password(nova_senha)
        
        user.save()
        
        # Registrar log no banco
        registrar_log(
            acao="Perfil atualizado",
            usuario=request.user,
            detalhes=f"Atualizou informações do perfil"
        )
        
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('perfil')
    
    return render(request, 'perfil.html')

def tabela_usuarios(request):
    """View para exibir tabela de usuários - BLOQUEADA para usuário comum"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.nivel_acesso == 'comum':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_comum')
    
    usuarios = CustomUser.objects.all().order_by('username')
    return render(request, 'tabela_usuarios.html', {'usuarios': usuarios})

# ============================================================================
# FUNÇÕES DE RECUPERAÇÃO DE SENHA
# ============================================================================

def esqueci_senha(request):
    """View para solicitar reset de senha"""
    if request.method == 'POST':
        email = request.POST['email']
        
        try:
            user = CustomUser.objects.get(email=email)
            
            import random
            token = str(random.randint(100000, 999999))
            
            request.session['reset_token'] = token
            request.session['reset_user_id'] = user.id
            request.session['token_expires'] = (timezone.now() + timezone.timedelta(minutes=15)).timestamp()
            
            send_mail(
                'Token de Reset - Sistema de Estoque',
                f'Seu token para redefinir a senha é: {token}\n\nEste token expira em 15 minutos.',
                config('DEFAULT_FROM_EMAIL', default='noreply@sistema.com'),
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Token enviado para seu email!')
            return redirect('verificar_token')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'Email não encontrado')
    
    return render(request, 'esqueci_senha.html')

def verificar_token(request):
    """View para verificar token enviado por email"""
    if 'reset_token' not in request.session:
        messages.error(request, 'Sessão expirada. Solicite um novo token.')
        return redirect('esqueci_senha')
    
    if timezone.now().timestamp() > request.session.get('token_expires', 0):
        del request.session['reset_token']
        del request.session['reset_user_id']
        del request.session['token_expires']
        messages.error(request, 'Token expirado. Solicite um novo token.')
        return redirect('esqueci_senha')
    
    if request.method == 'POST':
        token_digitado = request.POST['token']
        
        if token_digitado == request.session['reset_token']:
            return redirect('nova_senha')
        else:
            messages.error(request, 'Token inválido')
    
    return render(request, 'verificar_token.html')

def nova_senha(request):
    """View para definir nova senha após verificar token"""
    if 'reset_token' not in request.session or 'reset_user_id' not in request.session:
        messages.error(request, 'Sessão inválida. Inicie o processo novamente.')
        return redirect('esqueci_senha')
    
    if request.method == 'POST':
        nova_senha = request.POST['nova_senha']
        confirmar_senha = request.POST['confirmar_senha']
        
        if nova_senha != confirmar_senha:
            messages.error(request, 'Senhas não coincidem')
            return render(request, 'nova_senha.html')
        
        senha_valida, mensagem = validar_senha_forte(nova_senha)
        if not senha_valida:
            messages.error(request, mensagem)
            return render(request, 'nova_senha.html')
        
        user = CustomUser.objects.get(id=request.session['reset_user_id'])
        user.set_password(nova_senha)
        user.save()
        
        del request.session['reset_token']
        del request.session['reset_user_id']
        del request.session['token_expires']
        
        messages.success(request, 'Senha alterada com sucesso!')
        return redirect('login')
    
    return render(request, 'nova_senha.html')

# ============================================================================
# FUNÇÕES DE AUTENTICAÇÃO 2FA
# ============================================================================

def setup_totp(request):
    """Configuração inicial do TOTP"""
    if 'setup_user_id' not in request.session:
        return redirect('login')
    
    user = CustomUser.objects.get(id=request.session['setup_user_id'])
    
    if request.method == 'POST':
        try:
            import pyotp
            token = request.POST['token'].strip()
            
            if not user.totp_secret:
                messages.error(request, 'Erro: Secret TOTP não encontrado')
                return render(request, 'setup_totp.html')
            
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(token, valid_window=2):
                user.totp_enabled = True
                user.save()
                auth_login(request, user)
                del request.session['setup_user_id']
                messages.success(request, 'Autenticação 2FA configurada com sucesso!')
                if user.nivel_acesso == 'comum':
                    return redirect('dashboard_comum')
                elif user.nivel_acesso == 'admin':
                    return redirect('dashboard_admin')
                elif user.nivel_acesso == 'superadmin':
                    return redirect('dashboard_super')
            else:
                messages.error(request, 'Código inválido. Verifique se o código está correto e tente novamente.')
        except ImportError:
            messages.error(request, 'Erro: Biblioteca pyotp não instalada')
        except Exception as e:
            messages.error(request, f'Erro no 2FA: {str(e)}')
    
    if not user.totp_secret:
        import pyotp
        user.totp_secret = pyotp.random_base32()
        user.save()
    
    import pyotp
    import qrcode
    from io import BytesIO
    import base64
    
    totp = pyotp.TOTP(user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.username,
        issuer_name="Stock Flow"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'setup_totp.html', {
        'qr_code': qr_code,
        'secret': user.totp_secret
    })

def verify_totp(request):
    """Verificação do TOTP no login"""
    if 'login_user_id' not in request.session:
        return redirect('login')
    
    user = CustomUser.objects.get(id=request.session['login_user_id'])
    
    if request.method == 'POST':
        try:
            import pyotp
            token = request.POST['token'].strip()
            
            if not user.totp_secret:
                messages.error(request, 'Erro: Secret TOTP não encontrado')
                return render(request, 'verify_totp.html')
            
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(token, valid_window=2):
                auth_login(request, user)
                del request.session['login_user_id']
                
                # Registrar log de login no banco
                registrar_log(
                    acao="Login realizado",
                    usuario=user,
                    detalhes=f"Login feito com sucesso pelo usuário {user.username} | IP: {request.META.get('REMOTE_ADDR')}"
                )
                
                if user.nivel_acesso == 'comum':
                    return redirect('dashboard_comum')
                elif user.nivel_acesso == 'admin':
                    return redirect('dashboard_admin')
                elif user.nivel_acesso == 'superadmin':
                    return redirect('dashboard_super')
            else:
                messages.error(request, 'Código inválido. Verifique se o código está correto e tente novamente.')
        except ImportError:
            messages.error(request, 'Erro: Biblioteca pyotp não instalada')
        except Exception as e:
            messages.error(request, f'Erro no 2FA: {str(e)}')
    
    return render(request, 'verify_totp.html')

@login_required
def reset_user_totp(request, user_id):
    """Reset TOTP de outro usuário (apenas superadmin)"""
    if request.user.nivel_acesso != 'superadmin':
        messages.error(request, 'Acesso negado')
        return redirect('dashboard_super')
    
    user = get_object_or_404(CustomUser, id=user_id)
    user.totp_secret = None
    user.totp_enabled = False
    user.save()
    
    messages.success(request, f'Autenticação 2FA resetada para {user.username}')
    return redirect('dashboard_super')

@login_required
def deletar_conta(request):
    """View para deletar conta do usuário"""
    if request.method == 'POST':
        user = request.user
        username = user.username
        
        # Registrar log antes de deletar
        registrar_log(
            acao="Conta deletada",
            usuario=user,
            detalhes=f"Usuário {username} deletou sua própria conta"
        )
        
        # Anonimizar dados em todas as tabelas
        from .models import Entradas, Saidas, Solicitacao, Movimentacao, logs as LogsModel
        
        # Atualizar registros para "Usuário Excluído"
        Entradas.objects.filter(usuario=username).update(usuario="Usuário Excluído")
        Saidas.objects.filter(usuario=username).update(usuario="Usuário Excluído")
        Solicitacao.objects.filter(solicitante=username).update(solicitante="Usuário Excluído")
        Solicitacao.objects.filter(aprovador=username).update(aprovador="Usuário Excluído")
        Movimentacao.objects.filter(usuario=username).update(usuario="Usuário Excluído")
        LogsModel.objects.filter(usuario=username).update(usuario="Usuário Excluído")
        
        # Fazer logout e deletar usuário
        auth_logout(request)
        user.delete()
        
        messages.success(request, 'Sua conta foi excluída com sucesso.')
        return redirect('home')
    
    return redirect('perfil')