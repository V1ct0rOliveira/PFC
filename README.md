# Sistema de Estoque com 2FA

Sistema Django com autenticação em dois fatores via Twilio.

## Configuração

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Configurar banco de dados:**
```bash
python setup_db.py
```

3. **Criar superusuário:**
```bash
python manage.py createsuperuser
```

4. **Executar servidor:**
```bash
python manage.py runserver
```

## Funcionalidades

- ✅ Cadastro de usuários
- ✅ Login com autenticação 2FA via SMS
- ✅ Dashboard protegido
- ✅ Modelo de usuário customizado
- ✅ Interface responsiva com Bootstrap

## Configuração Twilio

As credenciais do Twilio já estão configuradas no arquivo `.env`:
- Account SID
- Auth Token  
- Verify Service SID

## Fluxo de Autenticação

1. Usuário faz cadastro
2. Usuário faz login (username/password)
3. Sistema solicita verificação 2FA
4. Código SMS é enviado via Twilio
5. Usuário insere código e acessa dashboard

## URLs Disponíveis

- `/` - Página inicial
- `/cadastro/` - Cadastro de usuário
- `/login/` - Login
- `/verify-2fa/` - Verificação 2FA
- `/dashboard/` - Dashboard (protegido)
- `/logout/` - Logout