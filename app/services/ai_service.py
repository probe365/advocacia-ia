import google.generativeai as genai
import os

class AIService:
    def __init__(self):
        # A chave deve estar no seu arquivo .env
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        model_name = (
            os.getenv("GOOGLE_GEMINI_MODEL")
            or os.getenv("GEMINI_MODEL")
            or "gemini-flash-latest"
        )
        self.model = genai.GenerativeModel(model_name)

    def call_gemini(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro na chamada da IA: {e}"