from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from twilio.rest import Client
from django.conf import settings
from .models import CustomUser
import json

def home(request):
    return render(request, 'home.html')

def cadastro(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        nome = request.POST['nome']
        sobrenome = request.POST['sobrenome']
        telefone = request.POST['telefone']
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Usuário já existe')
            return render(request, 'cadastro.html')
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            nome=nome,
            sobrenome=sobrenome,
            telefone=telefone,
            nivel_acesso='comum'
        )
        
        messages.success(request, 'Cadastro realizado com sucesso!')
        return redirect('login')
    
    return render(request, 'cadastro.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user:
            request.session['user_id'] = user.id
            request.session['requires_2fa'] = True
            return redirect('verify_2fa')
        else:
            messages.error(request, 'Credenciais inválidas')
    
    return render(request, 'login.html')

def verify_2fa(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = CustomUser.objects.get(id=request.session['user_id'])
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_code':
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                verification = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                    to=user.telefone,
                    channel='sms'
                )
                messages.success(request, 'Código enviado para seu telefone!')
                return render(request, 'verify_2fa.html', {'code_sent': True})
            except Exception as e:
                messages.error(request, f'Erro ao enviar código: {str(e)}')
        
        elif action == 'verify_code':
            code = request.POST['code']
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                verification_check = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
                    to=user.telefone,
                    code=code
                )
                
                if verification_check.status == 'approved':
                    auth_login(request, user)
                    user.is_verified = True
                    user.save()
                    del request.session['user_id']
                    del request.session['requires_2fa']
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Código inválido')
            except Exception as e:
                messages.error(request, f'Erro na verificação: {str(e)}')
    
    return render(request, 'verify_2fa.html')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def logout(request):
    auth_logout(request)
    return redirect('home')