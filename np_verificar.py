# procurar qualquer atribuição a "np" no arquivo
Select-String -Pattern '(^|\s)np\s*=' -List -CaseSensitive .\train_legal_w2v_bilstm.py

# também procura "for np in" e "def np("
Select-String -Pattern 'for\s+np\s+in|def\s+np\s*\(' -CaseSensitive .\train_legal_w2v_bilstm.py
