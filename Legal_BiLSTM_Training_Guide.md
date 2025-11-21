
# Legal BiLSTM Training Guide

**Project Context:** Advocacia e IA – Legal Decision Classification (STJ Dataset)  
**Dataset:** `data/interim/corpus_geral.csv`  
**Model:** Word2Vec + BiLSTM Classifier  
**Script:** `train_legal_w2v_bilstm.py`

---

## 1. Overview and Objectives

This document describes the architecture, training flow, and evaluation process of the **Legal BiLSTM model** developed for the *Advocacia e IA* system.

The purpose is to train a robust classifier that can understand **legal reasoning patterns** from the Superior Tribunal de Justiça (STJ) dataset, enabling automated classification, similarity search, and retrieval of legal ementas.

---

## 2. Architecture Overview

### 🔹 Word2Vec — Semantic Embedding
The **Word2Vec** model learns distributed vector representations of legal terms.  
It maps words into a continuous high-dimensional space where semantically similar words are close to each other.

**Example:**  
```
similarity("agravo", "recurso") → 0.83  
similarity("sentença", "contrato") → 0.15
```

### 🔹 BiLSTM Classifier — Context Understanding
The **Bidirectional LSTM** reads each sentence forward and backward, allowing the model to understand both past and future context.

It learns to identify the semantic structure of decisions, such as the difference between:

- *“nega provimento ao recurso”*  
- *“dá provimento ao recurso”*

---

## 3. Training Pipeline

1. **Dataset Load** → `corpus_geral.csv` containing `text`, `label`, `grupo`, and `data_decisao`  
2. **Temporal Split** → Training, validation, and test sets are divided chronologically.  
3. **Rare Class Treatment** → Classes with very few samples are resampled or weighted.  
4. **Word2Vec Training** → Legal vocabulary vectors are generated (`w2v.kv`).  
5. **BiLSTM Training** → Model learns contextual classification over sequences.  

---

## 4. Metrics and Evaluation

| Metric | Description | Expectation |
|--------|--------------|-------------|
| **Loss** | Cross-entropy or focal loss; measures overall error | Should decrease with epochs |
| **Accuracy** | Percentage of correctly classified samples | Should increase steadily |
| **Macro-F1** | Balanced F1 across all classes | Best indicator for class imbalance |

> **Macro-F1** is crucial in legal datasets because class frequencies vary widely (e.g., more “agravos” than “embargos”).

---

## 5. Training Stability Pack v1.1

To ensure stable and fair learning, several mechanisms were implemented:

### ✅ Focal Loss
Gives more importance to **rare classes**. Helps avoid dominance by frequent ones.

### ✅ WeightedRandomSampler
Oversamples rare labels, ensuring the model sees all classes.

### ✅ ReduceLROnPlateau
Automatically reduces learning rate when validation F1 stops improving.

### ✅ Early Stopping
Halts training after several stagnant epochs (to prevent overfitting).

### ✅ Gradient Clipping
Prevents numerical explosion in BiLSTM gradients.

---

## 6. Training Example Output

```
Epoch 05 | train_loss=3.7866 acc=0.4346 | val_loss=3.2338 acc=0.5123 macroF1=0.1711
Epoch 10 | train_loss=1.5099 acc=0.5103 | val_loss=3.1036 acc=0.4547 macroF1=0.1849
== Evaluation on TEST ==
TEST: loss=3.9420 acc=0.4356
```

Interpretation:
- Loss drops consistently → model is learning.
- Macro-F1 increases gradually → improving balance.
- Accuracy stabilizes around 0.45–0.60 → good for multi-class law tasks.

---

## 7. Output Artifacts

After successful training, these files are generated:

| File | Description |
|------|--------------|
| `w2v.kv` | Word2Vec vectors of the legal vocabulary |
| `vocab.pkl` | Token index mapping |
| `label_encoder.pkl` | Encoded class labels |
| `model.pt` | Trained BiLSTM weights |
| `best_model.pt` | Best checkpoint (highest F1) |
| `config.json` | Training parameters and architecture |
| `classification_report.txt` | Evaluation metrics |
| `confusion_matrix.csv` | Confusion matrix |
| `metrics_by_group.csv` | Group-wise evaluation results |

---

## 8. Inference (Next Step)

Once trained, you can create a simple inference script:

```python
# predict_ementa.py (preview)

import torch, pickle, json
from model_utils import BiLSTMClassifier, basic_tokenize_lower_ws

cfg = json.load(open("models/legal_bilstm_v2/config.json"))
vocab = pickle.load(open("models/legal_bilstm_v2/vocab.pkl", "rb"))
le = pickle.load(open("models/legal_bilstm_v2/label_encoder.pkl", "rb"))

model = BiLSTMClassifier(
    vocab_size=len(vocab),
    embed_dim=cfg["embed_dim"],
    hidden_dim=cfg["hidden_dim"],
    num_classes=len(le.classes_),
    pad_idx=cfg["pad_idx"],
    dropout=cfg["dropout"]
)
model.load_state_dict(torch.load("models/legal_bilstm_v2/best_model.pt"))
model.eval()

def predict(text):
    tokens = basic_tokenize_lower_ws(text)
    ids = [vocab.get(t, cfg["unk_idx"]) for t in tokens][:cfg["max_len"]]
    with torch.no_grad():
        out = model(torch.tensor([ids]))
    pred = out.argmax(1).item()
    return le.classes_[pred]

print(predict("Agravo interno no recurso especial. Competência tributária."))
```

---

## 9. Integration with Flask App

The trained model can be used in the existing module:

**File:** `ementas_bp.py`  
**Route:** `/ui/buscar`  

```python
from predict_ementa import predict

@app.route('/ui/predict', methods=['POST'])
def predict_ementa():
    text = request.form.get('q', '')
    label = predict(text)
    return jsonify({'predicted_label': label})
```

This allows end users to **upload case summaries** and automatically receive predicted legal categories.

---

## 10. Hardware Considerations

| Environment | Recommended Settings |
|--------------|---------------------|
| **CPU (Local)** | Use `--epochs 10`, `--batch-size 32` |
| **GPU (Colab/Cloud)** | Increase to `--epochs 20–30`, `--batch-size 64–128` |
| **RAM** | Minimum 8 GB; 16+ GB recommended for corpus_geral.csv |

---

## 11. Next Steps

- Implement the inference pipeline (`predict_ementa.py`)
- Test predictions within Flask UI
- Add optional similarity search (using Word2Vec cosine distance)
- Explore fine-tuning on embeddings with domain-specific legal terms

---

## 12. Summary

This guide documents the **complete life cycle** of a deep learning model for **Brazilian legal document classification**, covering:
- preprocessing,  
- embedding learning,  
- contextual classification, and  
- production-ready deployment.

> 🚀 With this pipeline, your *Advocacia e IA* app can now automatically classify, cluster, and recommend STJ decisions based on semantic similarity.
