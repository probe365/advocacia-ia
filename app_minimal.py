# app_minimal.py - Versão leve para desenvolvimento (sem AI/ML pesados)
# Advocacia e IA - DIA 1 (12/11/2025)
# Use este durante desenvolvimento para testes rápidos de UI/CRUD

import os
os.environ['MINIMAL_MODE'] = '1'  # Flag para desabilitar modelos pesados

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  ADVOCACIA E IA - MODO DESENVOLVIMENTO (MINIMAL)")
    print("="*60)
    print("\n  [INFO] Modelos AI/ML desabilitados para startup rápido")
    print("  [INFO] Funcionalidades CRUD/Forms totalmente funcionais")
    print("  [INFO] Ementas/Pipeline/BiLSTM: DESABILITADOS")
    print("\n  Acesse: http://localhost:5000")
    print("  Press CTRL+C to quit\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
