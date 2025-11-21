# -*- coding: utf-8 -*-
"""
Blueprint for legal text inference routes.
Integrates with LegalInferClient for classification and similarity search.
"""
from flask import Blueprint, request, jsonify
from legal_infer_client import LegalInferClient

bp = Blueprint('inference', __name__, url_prefix='/api')

# Initialize inference client
infer = LegalInferClient("http://127.0.0.1:8000")


@bp.route('/classify', methods=['POST'])
def classify_ementa():
    """
    Classify a legal text (ementa) using the trained BiLSTM model.
    
    Request JSON:
    {
        "text": "legal text to classify"
    }
    
    Returns:
    {
        "prediction": "class_name",
        "confidence": 0.95,
        ...
    }
    """
    try:
        text = request.json.get("text", "").strip()
        if not text:
            return jsonify({"error": "Text field is required and cannot be empty"}), 400
        
        res = infer.predict(text)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/search_similar', methods=['POST'])
def search_similar():
    """
    Search for similar legal documents using semantic similarity.
    
    Request JSON:
    {
        "query": "legal text to search",
        "k": 10  (optional, default=10)
    }
    
    Returns:
    {
        "results": [
            {"text": "...", "similarity": 0.92},
            ...
        ]
    }
    """
    try:
        query = request.json.get("query", "").strip()
        k = request.json.get("k", 10)
        
        if not query:
            return jsonify({"error": "Query field is required and cannot be empty"}), 400
        
        if not isinstance(k, int) or k < 1:
            return jsonify({"error": "k must be a positive integer"}), 400
        
        res = infer.similar(query, k=k)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
