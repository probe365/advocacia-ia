import os

import pytest

SHOULD_SKIP = os.getenv("RUN_PIPELINE_TESTS") != "1"
pytestmark = pytest.mark.skipif(
    SHOULD_SKIP,
    reason="Pipeline integration tests require RUN_PIPELINE_TESTS=1 and real services",
)


def _load_pipeline():
    from utils.pipeline import Pipeline

    return Pipeline

def test_firac_integrity():
    pipeline_cls = _load_pipeline()
    pipeline = pipeline_cls(case_id="TESTE")
    firac_result = pipeline.generate_firac()
    firac_data = firac_result.get('data', {"facts": "", "issue": "", "rules": "", "application": "", "conclusion": ""})
    for campo in ["facts", "issue", "rules", "application", "conclusion"]:
        assert campo in firac_data, f"Campo '{campo}' não encontrado no resultado FIRAC. FIRAC: {firac_data}"
        assert firac_data[campo] and firac_data[campo] != "[DADO NÃO DISPONÍVEL]", f"Campo '{campo}' está vazio ou padrão no resultado FIRAC. FIRAC: {firac_data}"