# Sistema Web de Gerenciamento de Estoque

Sistema desenvolvido por **Victor Oliveira** e **Vinicius Nascimento**, com orientação de **Fabiano Bezerra**, como parte do bacharelado em Engenharia de Software na **Universidade de Mogi das Cruzes**.

## 🚀 Instalação e Configuração

### 1. Criar ambiente virtual
```bash
python -m venv venv
```

### 2. Ativar ambiente virtual
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Criar arquivo .env
Crie um arquivo `.env` na raiz do projeto com:
```bash
# Configurações Twilio (para 2FA)
TWILIO_ACCOUNT_SID=seu_account_sid
TWILIO_AUTH_TOKEN=seu_auth_token
TWILIO_VERIFY_SID=seu_verify_sid

# Configurações do Supabase
DB_NAME=nome_do_database
DB_USER=nome_do_user
DB_PASSWORD=sua_senha
DB_HOST=host_do_banco
DB_PORT=porta_do_banco
```

### 5. Configurar banco de dados
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Executar o sistema
```bash
# Comando único que inicia tudo
python manage.py runserver
```

**Acesse:**
- Interface Web: http://localhost:5000
- Admin Django: http://localhost:8000/admin

## 📊 Funcionalidades

### Níveis de Acesso
- **Usuário Comum**: Visualizar estoque e solicitar retiradas
- **Administrador**: Controle total do estoque e produtos
- **Superadministrador**: Todas as permissões + logs e gestão de usuários

### Recursos Principais
- ✅ Gestão completa de produtos
- ✅ Movimentações (entradas, saídas, ajustes)
- ✅ Dashboard com estatísticas em tempo real
- ✅ Autenticação 2FA via SMS (Twilio)
- ✅ Notificações de estoque baixo
- ✅ Relatórios em PDF, Excel e Word
- ✅ Interface responsiva com Bootstrap 5
- ✅ Logs de atividades detalhados

## 🔧 Tecnologias

- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: Flask + Jinja2 + Bootstrap 5
- **Banco**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Autenticação**: JWT + Twilio 2FA
- **Relatórios**: python-docx, openpyxl, reportlab

## 📝 URLs Disponíveis

- **Interface Web**: http://localhost:5000
- **API REST**: http://localhost:8000/api
- **Admin Django**: http://localhost:8000/admin