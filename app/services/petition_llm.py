from __future__ import annotations
from typing import Dict, Any
import re

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def _clean_llm_response(text: str, response_type: str = "general") -> str:
    if not text:
        return ""
    cleaned = text.strip()
    unwanted = [
        r"^Para fundamentar.*?são:\s*",
        r"^Com base.*?seguir:\s*",
        r"^Os principais artigos.*?são:\s*",
        r"^Certamente[,!.]?\s*",
        r"^Claro[,!.]?\s*",
        r"^Aqui está.*?:\s*",
        r"^Segue.*?:\s*",
    ]
    for pat in unwanted:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

    if response_type == "artigos":
        cleaned = re.sub(r"\*\*", "", cleaned)
        cleaned = re.sub(r"\s*-\s*[^,;\n]+(?=[,;\n]|$)", "", cleaned)
        cleaned = re.sub(r"^\d+\.\s*", "", cleaned, flags=re.MULTILINE)
        lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
        if lines:
            artigos = []
            for line in lines:
                if re.search(r"\bArt\.?\s*\d+", line, flags=re.IGNORECASE):
                    artigos.append(line)
            cleaned = ", ".join(artigos[:8]) if artigos else lines[0]
    return cleaned.strip()

class PetitionLLM:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        # ajuste o model conforme sua conta
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self._init_prompts()

    def _init_prompts(self) -> None:
        self.NOME_ACAO = PromptTemplate(
            input_variables=["firac_issue", "firac_conclusion"],
            template=(
                'Questão jurídica: "{firac_issue}"\n'
                'Conclusão: "{firac_conclusion}"\n\n'
                "Gere APENAS o nome formal da ação judicial em PORTUGUÊS, sem explicações.\n"
                'Resposta (SOMENTE o nome da ação):'
            ),
        )

        self.ARTIGOS = PromptTemplate(
            input_variables=["firac_rules"],
            template=(
                "Com base nas seguintes regras e normas identificadas:\n{firac_rules}\n\n"
                "Liste APENAS os artigos de lei, de forma concisa. Formato: "
                '"Art. X do [Lei], Art. Y do [Lei]". Sem explicações.\n'
                "Resposta (SOMENTE os artigos):"
            ),
        )

        self.FATOS = PromptTemplate(
            input_variables=["firac_facts"],
            template=(
                "Os fatos relevantes são:\n{firac_facts}\n\n"
                'Reescreva como narrativa coesa e formal para a seção "DOS FATOS" de petição inicial.\n'
                "Narrativa dos Fatos:"
            ),
        )

        self.DIREITO = PromptTemplate(
            input_variables=["firac_issue", "firac_rules", "firac_application"],
            template=(
                'Para uma petição inicial, redija a seção "DO DIREITO".\n'
                "Questão: {firac_issue}\n"
                "Regras: {firac_rules}\n"
                "Aplicação: {firac_application}\n\n"
                "Estruture de forma lógica e persuasiva (pode usar subseções). Responda em PT-BR.\n"
                "Texto DO DIREITO:"
            ),
        )

        self.PEDIDOS = PromptTemplate(
            input_variables=["firac_conclusion", "firac_issue"],
            template=(
                'A conclusão FIRAC para a questão "{firac_issue}" é:\n{firac_conclusion}\n\n'
                'Formule TODOS os pedidos para "DOS PEDIDOS".\n'
                'Um pedido por linha, com alíneas "a) ...;", "b) ...;" etc.\n'
                "Inclua: citação, procedência, custas/honorários, provas.\n\n"
                "LISTA DE PEDIDOS:"
            ),
        )

    def _invoke(self, prompt: PromptTemplate, inputs: Dict[str, Any], response_type: str = "general") -> str:
        rendered = prompt.format(**inputs)
        resp = self.llm.invoke(rendered)
        text = getattr(resp, "content", "")
        text = text.strip() if isinstance(text, str) else str(text).strip()
        return _clean_llm_response(text, response_type=response_type)

    def build_sections(self, firac: Dict[str, str]) -> Dict[str, str]:
        issue = firac.get("issue", "") or ""
        conclusion = firac.get("conclusion", "") or ""
        rules = firac.get("rules", "") or ""
        facts = firac.get("facts", "") or ""
        application = firac.get("application", "") or ""

        return {
            "nome_acao": self._invoke(self.NOME_ACAO, {"firac_issue": issue, "firac_conclusion": conclusion}, "general").upper(),
            "artigos": self._invoke(self.ARTIGOS, {"firac_rules": rules}, "artigos"),
            "dos_fatos": self._invoke(self.FATOS, {"firac_facts": facts}, "general"),
            "do_direito": self._invoke(self.DIREITO, {"firac_issue": issue, "firac_rules": rules, "firac_application": application}, "general"),
            "pedidos": self._invoke(self.PEDIDOS, {"firac_conclusion": conclusion, "firac_issue": issue}, "general"),
        }
