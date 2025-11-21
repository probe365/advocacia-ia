def test_sanitizacao_danos_materiais():
    narrativa = "O produto apresentou defeito após 3 dias de uso. O fabricante se recusou a realizar o reembolso."
    fatos = "O autor comprou um produto eletrônico que apresentou defeito. Tentou contato com o fabricante, sem sucesso."
    resultado = _sanitize_narrativa(narrativa, fatos, contexto="consumo")
    assert "produto" in resultado
    assert "reembolso" in resultado

def test_sanitizacao_honorarios_advocaticios():
    narrativa = "O autor busca substituição de produto defeituoso adquirido em loja física."
    fatos = "O autor é advogado público e atuou em processo judicial que resultou em condenação da parte ré."
    resultado = _sanitize_narrativa(narrativa, fatos, contexto="honorários")
    assert "produto" not in resultado
    assert "advogado público" in resultado

def test_sanitizacao_fallback():
    narrativa = "Texto irrelevante sem conexão com os fatos."
    fatos = "O réu deixou de pagar os honorários sucumbenciais conforme sentença transitada em julgado."
    resultado = _sanitize_narrativa(narrativa, fatos, contexto="cível")
    assert "honorários sucumbenciais" in resultado
