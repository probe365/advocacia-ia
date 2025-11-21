from utils.pipeline import Pipeline

def test_firac_integrity():
    pipeline = Pipeline(case_id="TESTE")
    firac_result = pipeline.generate_firac()
    firac_data = firac_result.get('data', {"facts": "", "issue": "", "rules": "", "application": "", "conclusion": ""})
    for campo in ["facts", "issue", "rules", "application", "conclusion"]:
        assert campo in firac_data, f"Campo '{campo}' não encontrado no resultado FIRAC. FIRAC: {firac_data}"
        assert firac_data[campo] and firac_data[campo] != "[DADO NÃO DISPONÍVEL]", f"Campo '{campo}' está vazio ou padrão no resultado FIRAC. FIRAC: {firac_data}"