import secrets

# Usa o módulo `os` para gerar dados aleatórios
import os
secret_key = os.urandom(32)
print(secret_key)