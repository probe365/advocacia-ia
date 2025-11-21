# Configuração de Email para Upload em Massa

Este arquivo contém exemplos de como configurar a notificação por email para diferentes provedores.

---

## ⚙️ Configuração Geral

### Localização do Arquivo .env

```
c:\adv-IA-F\.env
```

### Variáveis Necessárias

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_ou_app_password
EMAIL_FROM=seu_email@gmail.com
SMTP_USE_TLS=true
```

---

## 📧 Configurações por Provedor

### 1️⃣ Gmail (Google Workspace)

#### Pré-requisitos:
- Conta Google ativa
- Autenticação em 2 fatores habilitada (recomendado)

#### Passos:

1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "Mail" e "Windows"
3. Copie a senha gerada (16 caracteres com espaços)
4. Configure o arquivo `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Copie aqui
EMAIL_FROM=seu_email@gmail.com
SMTP_USE_TLS=true
```

#### Teste:
```python
# Executar no terminal
python
>>> import smtplib
>>> server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
>>> server.starttls()
>>> server.login("seu_email@gmail.com", "xxxx xxxx xxxx xxxx")
>>> print("✓ Conectado com sucesso!")
>>> server.quit()
```

---

### 2️⃣ Outlook / Microsoft 365

#### Configuração:

```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=seu_email@outlook.com
SMTP_PASSWORD=sua_senha_outlook
EMAIL_FROM=seu_email@outlook.com
SMTP_USE_TLS=true
```

#### Ou com Microsoft 365:

```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=seu_email@empresa.com
SMTP_PASSWORD=sua_senha_corporativa
EMAIL_FROM=seu_email@empresa.com
SMTP_USE_TLS=true
```

---

### 3️⃣ Hosted Email (Hostgator, GoDaddy, etc)

#### Configuração Genérica:

```bash
SMTP_HOST=smtp.seudominio.com
SMTP_PORT=587
SMTP_USER=email@seudominio.com
SMTP_PASSWORD=sua_senha_email
EMAIL_FROM=noreply@seudominio.com
SMTP_USE_TLS=true
```

#### Exemplo Hostgator:

```bash
SMTP_HOST=secure.emailsrvr.com
SMTP_PORT=465
SMTP_USER=seu_email@seudominio.com
SMTP_PASSWORD=sua_senha
EMAIL_FROM=seu_email@seudominio.com
SMTP_USE_TLS=false  # Hostgator usa SSL direto na porta 465
```

---

### 4️⃣ SendGrid (Recomendado para Produção)

#### Pré-requisitos:
- Conta SendGrid: https://sendgrid.com
- API Key gerada

#### Configuração:

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey  # Sempre "apikey"
SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Sua API Key
EMAIL_FROM=seu_email_verificado@seudominio.com
SMTP_USE_TLS=true
```

#### Vantagens:
- ✅ Alta entregabilidade
- ✅ Rastreamento de emails
- ✅ Analytics
- ✅ Plano gratuito (100 emails/dia)

---

### 5️⃣ Mailgun

#### Pré-requisitos:
- Conta Mailgun: https://www.mailgun.com
- Domínio verificado

#### Configuração:

```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@seu_dominio_mg.mailgun.org
SMTP_PASSWORD=sua_password_mailgun
EMAIL_FROM=noreply@seu_dominio_mg.mailgun.org
SMTP_USE_TLS=true
```

---

### 6️⃣ Desenvolvimento Local (Mailtrap)

#### Para Testes sem Enviar Realmente:

1. Acesse: https://mailtrap.io
2. Crie uma conta gratuita
3. Configure como abaixo:

```bash
SMTP_HOST=live.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=seu_usuario_mailtrap
SMTP_PASSWORD=sua_password_mailtrap
EMAIL_FROM=seu_email@mailtrap.io
SMTP_USE_TLS=true
```

#### Vantagens para Dev:
- ✅ Não envia email real
- ✅ Captura todos os emails
- ✅ Visualiza HTML no navegador
- ✅ Perfeito para testes

---

## 🧪 Testando a Configuração

### Teste 1: Verificar Configuração no Código

Criar arquivo `test_email.py`:

```python
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Carregar variáveis
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

print(f"Testando SMTP...")
print(f"  HOST: {SMTP_HOST}")
print(f"  PORT: {SMTP_PORT}")
print(f"  USER: {SMTP_USER}")
print(f"  FROM: {EMAIL_FROM}")
print(f"  TLS: {SMTP_USE_TLS}")

try:
    # Conectar
    print("\n1. Conectando ao servidor...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    print("   ✓ Conectado")
    
    # TLS
    if SMTP_USE_TLS:
        print("2. Iniciando TLS...")
        server.starttls()
        print("   ✓ TLS iniciado")
    
    # Login
    print("3. Fazendo login...")
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("   ✓ Autenticado")
    
    # Fechar
    print("4. Fechando conexão...")
    server.quit()
    print("   ✓ Desconectado")
    
    print("\n✅ Teste SUCESSO! Email está configurado corretamente.")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ ERRO DE AUTENTICAÇÃO: {e}")
    print("   Verifique SMTP_USER e SMTP_PASSWORD")
    
except smtplib.SMTPException as e:
    print(f"\n❌ ERRO SMTP: {e}")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
```

Executar:
```bash
cd c:\adv-IA-F
python test_email.py
```

### Teste 2: Enviar Email de Teste

Criar arquivo `send_test_email.py`:

```python
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuração
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
EMAIL_FROM = os.getenv('EMAIL_FROM')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

# Email de destino (MUDE AQUI)
EMAIL_TO = "seu_email_teste@gmail.com"

try:
    # Criar mensagem
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Teste de Email - Advocacia e IA'
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    
    # Corpo HTML
    html = f"""
    <html>
        <body style="font-family: Arial;">
            <h2>Teste de Email</h2>
            <p>Se você recebeu este email, a configuração SMTP está funcionando!</p>
            <div style="background-color: #f0f0f0; padding: 10px; margin: 20px 0;">
                <p><strong>Data/Hora:</strong> {os.popen('date').read().strip()}</p>
                <p><strong>Host:</strong> {SMTP_HOST}</p>
                <p><strong>User:</strong> {SMTP_USER}</p>
            </div>
            <p>✓ Teste realizado com sucesso!</p>
        </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    
    # Conectar e enviar
    print(f"Enviando email para {EMAIL_TO}...")
    
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    if SMTP_USE_TLS:
        server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()
    
    print("✅ Email enviado com sucesso!")
    print(f"Verifique sua caixa de entrada: {EMAIL_TO}")
    
except Exception as e:
    print(f"❌ Erro ao enviar: {e}")
```

Executar:
```bash
cd c:\adv-IA-F
python send_test_email.py
```

---

## 🛡️ Segurança

### ✅ Práticas Recomendadas

1. **Nunca commitar .env**
   ```bash
   # .gitignore
   .env
   .env.local
   *.env
   ```

2. **Usar Variáveis de Ambiente**
   ```bash
   # NÃO FAÇA:
   password = "minha_senha_123"
   
   # FAÇA:
   password = os.getenv('SMTP_PASSWORD')
   ```

3. **Senhas de App (Gmail, Microsoft)**
   - Usar senha de app, não senha principal
   - Regenerar periodicamente
   - Revogar se comprometida

4. **SMTP sobre TLS**
   - Sempre usar `SMTP_USE_TLS=true`
   - Protege credenciais em trânsito

5. **Logs**
   ```python
   # NÃO FAÇA:
   print(f"Conectando com {password}")
   
   # FAÇA:
   logger.info("Conectando ao SMTP")
   ```

---

## 📋 Checklist de Configuração

- [ ] Arquivo `.env` criado em `c:\adv-IA-F`
- [ ] Variáveis `SMTP_HOST`, `SMTP_PORT`, etc. preenchidas
- [ ] Teste de conexão executado com sucesso (`test_email.py`)
- [ ] Teste de envio executado (`send_test_email.py`)
- [ ] Email recebido com sucesso
- [ ] `.env` adicionado ao `.gitignore`
- [ ] Aplicação reiniciada para carregar novas variáveis
- [ ] Upload em massa realizado
- [ ] Botão "Enviar Relatório por Email" aparece
- [ ] Email recebido com relatório

---

## ❌ Troubleshooting

### Erro: "Connection refused"
```
Solução: Verifique SMTP_HOST e SMTP_PORT
- HOST incorreto?
- PORT bloqueada pelo firewall?
- Servidor SMTP parado?
```

### Erro: "Authentication failed"
```
Solução: Verifique SMTP_USER e SMTP_PASSWORD
- Usuário correto?
- Senha correta?
- Senha de app (não senha principal)?
- Conta bloqueada?
```

### Erro: "TLS required"
```
Solução: Defina SMTP_USE_TLS=true ou use SSL
- Muitos servers modernos exigem TLS
- Porta 587 = TLS
- Porta 465 = SSL
```

### Email não chega na Caixa de Entrada
```
Solução:
1. Verifique pasta de Spam/Lixo
2. Verifique if SPF/DKIM/DMARC configurados (sendgrid, mailgun)
3. Use remetente verificado (não genérico)
4. Verifique headers do email
```

### Aplicação ignora erros de email
```
Solução: Esperado!
- Upload NÃO é bloqueado por erro de email
- Verifique logs em app/logs/
- Configure alertas para erros
```

---

## 🔗 Referências

- [Python smtplib docs](https://docs.python.org/3/library/smtplib.html)
- [Gmail app passwords](https://myaccount.google.com/apppasswords)
- [SendGrid SMTP](https://sendgrid.com/docs/for-developers/sending-email/smtp/)
- [Mailgun SMTP](https://documentation.mailgun.com/en/latest/api-sending.html)
- [Mailtrap (testing)](https://mailtrap.io)

---

**Última Atualização:** 16 de Outubro de 2025  
**Versão:** 1.0
