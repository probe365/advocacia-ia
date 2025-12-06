# 🚀 INICIAR FLASK - GUIA RÁPIDO

## Opção 1: MODO DESENVOLVIMENTO (RECOMENDADO) ⚡

**Startup rápido (~3-5 segundos) - ideal para testar Item 1 e Item 3**

```powershell
python app_minimal.py
```

**O que funciona:**
- ✅ Login/Auth
- ✅ CRUD Clientes
- ✅ CRUD Processos (com 12 novos campos)
- ✅ CRUD Partes Adversas (novo!)
- ✅ Escritório/Documentos
- ✅ Health checks

**O que NÃO funciona:**
- ❌ Ementas/FAISS (requer modelos AI)
- ❌ Pipeline/BiLSTM (requer gensim/transformers)
- ❌ Chat IA (requer OpenAI)

---

## Opção 2: MODO COMPLETO (PRODUÇÃO) 🎯

**Startup lento (~30-60 segundos) - carrega todos modelos AI/ML**

### Usando script automatizado:
```powershell
.\start_flask.ps1
```

### Manualmente:
```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

**Tudo funciona, incluindo:**
- ✅ Todos recursos do Modo Desenvolvimento
- ✅ Ementas FAISS (busca similaridade)
- ✅ Pipeline completo (ingestion, analysis, petition)
- ✅ BiLSTM Word2Vec (classificação legal)
- ✅ Chat IA com RAG

---

## 🔧 TROUBLESHOOTING

### Erro: "ModuleNotFoundError"
```powershell
pip install -r requirements.txt
```

### PostgreSQL não conecta
1. Verifique se PostgreSQL 17 está rodando
2. Confirme credenciais em `.env`
3. Teste: `psql -U postgres -d advocacia_ia`

### FFmpeg ausente (opcional)
- Vídeos desabilitados automaticamente
- Para habilitar: instale FFmpeg e adicione ao PATH

---

## 📋 TESTES DIA 1

### Testar Item 1 - Novos Campos Processos
1. Inicie: `python app_minimal.py`
2. Acesse: http://localhost:5000
3. Login: `admin@teste.com` / sua senha
4. Menu → Processos → Novo Processo
5. Preencha 12 novos campos (area_atuacao, comarca, etc)
6. Salvar e verificar no banco

### Testar Item 3 - CRUD Partes Adversas
1. Abra processo existente
2. Botão "Partes Adversas"
3. Adicionar 3 partes:
   - Autor (PF) - CPF válido
   - Réu (PJ) - CNPJ válido
   - Terceiro
4. Testar CEP autocomplete
5. Editar/Excluir

---

## 🆘 SUPORTE

**Logs em tempo real:**
```powershell
Get-Content flask_startup.log -Wait -Tail 50
```

**Parar Flask:**
- CTRL + C no terminal
- Ou: `Get-Process python | Stop-Process -Force`

---

**DIA 1 - 12/11/2025**  
**Próximo:** DIA 2 (Item 2 - CNJ imutável após distribuição)
