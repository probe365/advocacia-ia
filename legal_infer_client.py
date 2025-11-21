# -*- coding: utf-8 -*-
"""
Tiny Python client for legal_infer_api.py
Used by your main Flask app (Advocacia e IA)
"""

import json
import requests
from typing import List, Dict, Any, Optional


class LegalInferClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    # ------------------------------
    # Health check
    # ------------------------------
    def health(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/health", timeout=5)
        r.raise_for_status()
        return r.json()

    # ------------------------------
    # Predict (classify one ementa)
    # ------------------------------
    def predict(self, text: str) -> Dict[str, Any]:
        payload = {"text": text}
        r = requests.post(f"{self.base_url}/predict", json=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    # ------------------------------
    # Batch predict (list of ementas)
    # ------------------------------
    def batch_predict(self, texts: List[str]) -> List[Dict[str, Any]]:
        payload = {"texts": texts}
        r = requests.post(f"{self.base_url}/batch_predict", json=payload, timeout=20)
        r.raise_for_status()
        return r.json()

    # ------------------------------
    # Index new ementas for similarity search
    # ------------------------------
    def index_docs(self, docs: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        docs: list of {"id": "...", "text": "..."}
        """
        payload = {"docs": docs}
        r = requests.post(f"{self.base_url}/index", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    # ------------------------------
    # Search similar ementas
    # ------------------------------
    def similar(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        payload = {"query": query, "k": k}
        r = requests.post(f"{self.base_url}/similar", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()

    # ------------------------------
    # Reset the semantic index
    # ------------------------------
    def reset_index(self) -> Dict[str, Any]:
        r = requests.post(f"{self.base_url}/reset_index", timeout=5)
        r.raise_for_status()
        return r.json()
