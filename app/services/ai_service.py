import os
from typing import Optional

import google.generativeai as genai

class AIService:
    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não configurada")

        genai.configure(api_key=api_key)
        model_name = (
            os.getenv("GOOGLE_GEMINI_MODEL")
            or os.getenv("GEMINI_MODEL")
            or "gemini-flash-latest"
        )
        self.model = genai.GenerativeModel(model_name)

    def call_gemini(self, prompt: str) -> str:
        return self._safe_generate(prompt)

    def _safe_generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text or ""
        except Exception as exc:
            return f"Erro na chamada da IA: {exc}"