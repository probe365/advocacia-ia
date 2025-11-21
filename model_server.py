# model_server.py
import os
import json
import torch
import torch.nn as nn
import numpy as np
import pickle
from gensim.models import KeyedVectors
from threading import Lock

# ---------- BiLSTM (mesma arquitetura do trainer) ----------
class BiLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, pad_idx=0, w2v_weights=None, freeze_embeddings=False, num_layers=1, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        if w2v_weights is not None:
            self.embedding.weight.data.copy_(torch.from_numpy(w2v_weights))
        self.embedding.weight.requires_grad = not freeze_embeddings
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=True, num_layers=num_layers, dropout=dropout if num_layers>1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim*2, num_classes)

    def forward(self, x, lengths=None):
        emb = self.embedding(x)
        out, _ = self.lstm(emb)
        # pooling simples: max-pool ao longo do tempo
        x_max, _ = torch.max(out, dim=1)
        x = self.dropout(x_max)
        return self.fc(x)

# ---------- utilidades ----------
def pad_sequence(ids, max_len, pad=0):
    ids = ids[:max_len]
    if len(ids) < max_len:
        ids = ids + [pad]*(max_len-len(ids))
    return ids

class _ModelServer:
    def __init__(self):
        self._loaded = False
        self._lock = Lock()

    def load(self, models_dir="models/legal_bilstm"):
        with self._lock:
            if self._loaded:
                return

            cfg_path   = os.path.join(models_dir, "config.json")
            vocab_path = os.path.join(models_dir, "vocab.pkl")
            le_path    = os.path.join(models_dir, "label_encoder.pkl")
            w2v_path   = os.path.join(models_dir, "w2v.kv")
            model_path = os.path.join(models_dir, "model.pt")

            with open(cfg_path, "r", encoding="utf-8") as f:
                self.cfg = json.load(f)

            with open(vocab_path, "rb") as f:
                self.vocab = pickle.load(f)           # dict: token -> id
            with open(le_path, "rb") as f:
                self.label_encoder = pickle.load(f)   # sklearn LabelEncoder ou similar

            # monta matriz de embedding a partir do W2V
            kv = KeyedVectors.load(w2v_path, mmap='r')
            embed_dim = kv.vector_size
            vocab_size = max(self.vocab.values()) + 1
            pad_idx = self.cfg.get("pad_idx", 0)
            w2v_weights = np.random.normal(0, 0.1, size=(vocab_size, embed_dim)).astype(np.float32)
            # preenche pesos com vetores do w2v quando existir
            for tok, idx in self.vocab.items():
                if tok in kv:
                    w2v_weights[idx] = kv[tok]

            num_classes = len(self.label_encoder.classes_)
            hidden_dim = self.cfg.get("hidden_dim", 128)
            num_layers = self.cfg.get("num_layers", 1)
            dropout    = self.cfg.get("dropout", 0.2)
            freeze_emb = self.cfg.get("freeze_embeddings_at_infer", True)
            self.max_len = self.cfg.get("max_len", 400)

            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = BiLSTMClassifier(
                vocab_size=vocab_size,
                embed_dim=embed_dim,
                hidden_dim=hidden_dim,
                num_classes=num_classes,
                pad_idx=pad_idx,
                w2v_weights=w2v_weights,
                freeze_embeddings=freeze_emb,
                num_layers=num_layers,
                dropout=dropout,
            ).to(self.device)

            state = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state)
            self.model.eval()

            # tokenizer simples baseada em vocab (mesma do treino)
            self.unk_idx = self.cfg.get("unk_idx", 1)
            self.pad_idx = pad_idx
            self._loaded = True

    def _tokenize(self, text: str):
        # mesma normalização usada no treino (simplificada)
        t = (text or "").lower().strip()
        # split por espaço — se no treino houve regex/tokenização especial, replique aqui
        toks = t.split()
        ids = [ self.vocab.get(tok, self.unk_idx) for tok in toks ]
        return pad_sequence(ids, self.max_len, pad=self.pad_idx)

    def predict(self, text: str):
        if not self._loaded:
            self.load()

        ids = self._tokenize(text)
        x = torch.tensor([ids], dtype=torch.long, device=self.device)
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
            idx = int(np.argmax(probs))
            label = self.label_encoder.inverse_transform([idx])[0]
        # top-5
        topk = min(5, len(probs))
        top_idx = np.argsort(probs)[::-1][:topk]
        top = [(self.label_encoder.inverse_transform([i])[0], float(probs[i])) for i in top_idx]
        return label, top

# singleton
model_server = _ModelServer()
