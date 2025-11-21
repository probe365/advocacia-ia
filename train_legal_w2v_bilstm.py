# -*- coding: utf-8 -*-
import os, re, json, argparse, random, pickle
from datetime import datetime
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_class_weight
from sklearn.utils.multiclass import unique_labels

from sklearn.metrics import f1_score

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler

from gensim.models import Word2Vec, KeyedVectors

# --------------------------
# Utils e seed
# --------------------------
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def basic_tokenize_lower_ws(text):
    if not isinstance(text, str):
        return []
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text.split(" ")

# --------------------------
# Dataset e collation
# --------------------------
class TextDataset(Dataset):
    def __init__(self, df, text_col, y_col, vocab, max_len):
        self.df = df.reset_index(drop=True)
        self.text_col = text_col
        self.y_col = y_col
        self.vocab = vocab
        self.max_len = max_len

    def __len__(self):
        return len(self.df)

    def _encode(self, tokens):
        ids = [self.vocab.get(tok, self.vocab["<unk>"]) for tok in tokens]
        if len(ids) < self.max_len:
            ids = ids + [self.vocab["<pad>"]] * (self.max_len - len(ids))
        else:
            ids = ids[:self.max_len]
        return np.array(ids, dtype=np.int64)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        toks = basic_tokenize_lower_ws(row[self.text_col])
        x = self._encode(toks)
        y = int(row[self.y_col])
        return torch.from_numpy(x), torch.tensor(y, dtype=torch.long)

# --------------------------
# Modelo BiLSTM
# --------------------------
class BiLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes,
                 pad_idx, w2v_weights=None, freeze_embeddings=True,
                 num_layers=1, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        if w2v_weights is not None:
            self.embedding.weight.data.copy_(torch.tensor(w2v_weights))
        self.embedding.weight.requires_grad = not freeze_embeddings

        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=(dropout if num_layers > 1 else 0.0),
            bidirectional=True
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(2 * hidden_dim, num_classes)

    def forward(self, x):
        emb = self.embedding(x)                # [B, T, E]
        out, _ = self.lstm(emb)                # [B, T, 2H]
        feat = out[:, -1, :]                   # último passo
        feat = self.dropout(feat)
        logits = self.fc(feat)                 # [B, C]
        return logits

# --------------------------
# Avaliação / Relatórios
# --------------------------
@torch.no_grad()
def evaluate(model, dl, criterion, device, diag_first_batch: bool = False):
    model.eval()
    total_loss, total_correct, total_seen = 0.0, 0, 0
    all_y, all_pred = [], []

    for i, (xb, yb) in enumerate(dl):
        xb, yb = xb.to(device), yb.to(device)
        out = model(xb)
        loss = criterion(out, yb)

        # Diagnóstico opcional: imprime apenas no 1º batch
        if diag_first_batch and i == 0:
            try:
                print(f"[diag] val batch loss={loss.item():.4f}, batch_size={xb.size(0)}")
            except Exception:
                pass

        total_loss += float(loss.item()) * xb.size(0)
        pred = out.argmax(1)
        total_correct += (pred == yb).sum().item()
        total_seen += xb.size(0)

        all_y.extend(yb.detach().cpu().numpy())
        all_pred.extend(pred.detach().cpu().numpy())

    loss = total_loss / max(total_seen, 1)
    acc = total_correct / max(total_seen, 1)
    return loss, acc, np.array(all_y), np.array(all_pred)


def save_confusion_matrix(y_true, y_pred, labels, out_csv):
    # salva contagens simples (não normalizadas) como CSV
    lab_to_idx = {i:i for i in range(len(labels))}
    mat = defaultdict(lambda: defaultdict(int))
    for yt, yp in zip(y_true, y_pred):
        mat[int(yt)][int(yp)] += 1
    rows = []
    for r in sorted(mat.keys()):
        row = {"true": r}
        for c in range(len(labels)):
            row[f"pred_{c}"] = mat[r].get(c, 0)
        rows.append(row)
    pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8")

def group_metrics(test_pred_df, le, out_csv):
    # Espera colunas: grupo, y_true, y_pred
    gm = (
        test_pred_df
        .groupby("grupo")
        .apply(lambda g: pd.Series({
            "macro_f1": f1_score(g["y_true"], g["y_pred"], average="macro", zero_division=0),
            "macro_precision": f1_score(g["y_true"], g["y_pred"], average="macro", zero_division=0, labels=unique_labels(g["y_true"], g["y_pred"])),
            "macro_recall": f1_score(g["y_true"], g["y_pred"], average="macro", zero_division=0, labels=unique_labels(g["y_true"], g["y_pred"])),
            "accuracy": (g["y_true"] == g["y_pred"]).mean()
        }))
        .reset_index()
    )
    gm.to_csv(out_csv, index=False, encoding="utf-8")
    return gm

# --------------------------
# Treino principal
# --------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-train-per-class", type=int, default=20,
                    help="Collapse tail classes into __OTHER__ if total samples < this value (default: 20)")
    parser.add_argument("--diag-val-loss", action="store_true",
                        help="Print first validation batch loss per epoch for diagnosis")

    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--text-col", type=str, default="text")
    parser.add_argument("--label-col", type=str, default="label")
    parser.add_argument("--grupo-col", type=str, default="grupo")
    parser.add_argument("--date-col", type=str, default="data_decisao")

    parser.add_argument("--models-dir", type=str, required=True)
    parser.add_argument("--max-len", type=int, default=400)
    parser.add_argument("--embed-dim", type=int, default=200)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--num-layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--freeze-emb-first", type=int, default=3)

    parser.add_argument("--cutoff", type=str, default="2022-12-31")  # split temporal
    parser.add_argument("--min-count", type=int, default=2)          # legado (mantido)
    parser.add_argument("--w2v-min-count", type=int, default=5)      # **novo**: W2V vocabulário
    parser.add_argument("--w2v-epochs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    set_seed(args.seed)

    os.makedirs(args.models_dir, exist_ok=True)
    out_reports = os.path.join(args.models_dir, "reports")
    os.makedirs(out_reports, exist_ok=True)

    print("== Carregando dataset ==")
    df = pd.read_csv(args.data)
    assert args.text_col in df.columns and args.label_col in df.columns, "Colunas de texto/label ausentes."

    # Split temporal (DEVE ser feito ANTES de processar tail classes)
    print("== Split temporal ==")
    df[args.date_col] = pd.to_datetime(df[args.date_col], errors="coerce")
    cutoff_dt = pd.to_datetime(args.cutoff)
    base_df = df[df[args.date_col] <= cutoff_dt].dropna(subset=[args.text_col, args.label_col]).copy()
    test_df = df[df[args.date_col] > cutoff_dt].dropna(subset=[args.text_col, args.label_col]).copy()

    # === Collapse tail classes into __OTHER__ (após criar base_df) ===
    MIN_TRAIN_PER_CLASS = args.min_train_per_class
    OTHER_TOKEN = "__OTHER__"

    freq_all = base_df[args.label_col].value_counts()
    tail = set(freq_all[freq_all < MIN_TRAIN_PER_CLASS].index)

    if len(tail) > 0:
        print(f"⚙️  Collapsing {len(tail)} tail classes (<{MIN_TRAIN_PER_CLASS} samples) into {OTHER_TOKEN}")
        base_df[args.label_col] = base_df[args.label_col].where(
            base_df[args.label_col].isin(tail),
            OTHER_TOKEN
        )

    # LabelEncoder
    le = LabelEncoder()
    base_df["_y"] = le.fit_transform(base_df[args.label_col].astype(str))
    test_df["_y"] = le.transform(test_df[args.label_col].astype(str))

    # Train/Val estratificado com “ajuste” p/ raras
    print("== Train/Val estratificado com tratamento de classes raras ==")
    from sklearn.model_selection import train_test_split

    # Preparar DataFrame base e rótulos
    df_trainval = base_df.copy()
    yb = df_trainval["_y"].values

    # Identificar classes com poucas amostras (<2)
    counts = df_trainval["_y"].value_counts()
    ok_mask = df_trainval["_y"].map(counts) >= 2
    df_ok   = df_trainval[ok_mask].copy()
    df_rare = df_trainval[~ok_mask].copy()

    if len(df_rare) > 0:
        print(f"⚠️ {len(df_rare)} linhas de {df_rare['_y'].nunique()} classes têm <2 amostras; "
            "elas irão apenas para TRAIN (não entram na validação).")

    # Split estratificado apenas nas classes com ≥2 amostras
    train_df, val_df = train_test_split(
        df_ok,
        test_size=0.10,
        random_state=args.seed,
        stratify=df_ok["_y"]
    )

    # Adicionar classes raras somente ao train
    train_df = pd.concat([train_df, df_rare], ignore_index=True)
    train_df = train_df.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)

    # Garantir que classes raras (suporte 1–2) estão no train
    rare_counts = train_df["_y"].value_counts()
    rare_in_train = (rare_counts[rare_counts <= 2]).sum()

    print("== Preparando conjunto de teste ==")
    Xt, yt = test_df[args.text_col].values, test_df["_y"].values
    print(f"Train: {len(train_df)} | Val: {len(val_df)} | (rare_in_train={rare_in_train})")


    # Treinar Word2Vec + vocabulário
    print("== Treinando Word2Vec e vocabulário ==")
    train_tokens = [basic_tokenize_lower_ws(t) for t in train_df[args.text_col].astype(str)]
    val_tokens   = [basic_tokenize_lower_ws(t) for t in val_df[args.text_col].astype(str)]
    test_tokens  = [basic_tokenize_lower_ws(t) for t in test_df[args.text_col].astype(str)]

    w2v = Word2Vec(
        sentences=train_tokens,
        vector_size=args.embed_dim,
        window=5,
        min_count=args.w2v_min_count,   # **novo**
        workers=1,
        epochs=args.w2v_epochs,
        sg=1
    )
    kv = w2v.wv

    # vocabulário
    vocab = {"<pad>":0, "<unk>":1}
    for tok, cnt in Counter([t for sent in train_tokens for t in sent]).items():
        if cnt >= args.min_count:
            if tok not in vocab:
                vocab[tok] = len(vocab)
    PAD_IDX = vocab["<pad>"]
    UNK_IDX = vocab["<unk>"]

    # Matriz de embeddings
    w2v_weights = np.random.normal(scale=0.02, size=(len(vocab), args.embed_dim)).astype(np.float32)
    for tok, idx in vocab.items():
        if tok in ["<pad>", "<unk>"]:
            continue
        if tok in kv.key_to_index:
            w2v_weights[idx] = kv[tok]
        else:
            pass  # fica aleatório normal

    # Datasets/Dataloaders
    train_df = train_df.reset_index(drop=True)
    val_df   = val_df.reset_index(drop=True)
    test_df  = test_df.reset_index(drop=True)

    train_df["_y"] = train_df["_y"].astype(int)
    val_df["_y"]   = val_df["_y"].astype(int)
    test_df["_y"]  = test_df["_y"].astype(int)

    train_ds = TextDataset(train_df, args.text_col, "_y", vocab, args.max_len)
    val_ds   = TextDataset(val_df,   args.text_col, "_y", vocab, args.max_len)
    test_ds  = TextDataset(test_df,  args.text_col, "_y", vocab, args.max_len)

    # Class weights (normalizados e “clamped”)
    print("== Calculando class weights ==")
    classes = np.unique(train_df["_y"].values)
    cw = compute_class_weight(class_weight="balanced", classes=classes, y=train_df["_y"].values)

    # Expande para todas as classes na ordem do encoder
    full_weights = np.ones(len(le.classes_), dtype=np.float32)
    for c, w in zip(classes, cw):
        full_weights[int(c)] = float(w)

    # Normaliza p/ média ~1 e limita extremos (mais conservador)
    w = torch.tensor(full_weights, dtype=torch.float)
    w = w * (len(w) / w.sum())           # média ~1
    w = torch.clamp(w, 0.25, 3.0)         # faixa segura
    

    # Modelo
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    class_weights = w.to(device)
    model = BiLSTMClassifier(
        vocab_size=len(vocab),
        embed_dim=args.embed_dim,
        hidden_dim=args.hidden_dim,
        num_classes=len(le.classes_),
        pad_idx=PAD_IDX,
        w2v_weights=w2v_weights,
        freeze_embeddings=True,
        num_layers=args.num_layers,
        dropout=args.dropout
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    print("== Treinando ==")

    # LOSS & SCHEDULER — sem smoothing por enquanto
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=1
    )

    # print("== Treinando ==")
    # LOSS & SCHEDULER
    # criterion = nn.CrossEntropyLoss(
        # weight=class_weights.to(device),
        # label_smoothing=0.1
    # )
    # scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        # optimizer, mode="max", factor=0.5, patience=1
    # )
    # Early stopping
    best_val_f1, best_epoch, patience, no_improve = 0.0, 0, 2, 0
    best_state = None

    # Oversampling
    freq = train_df["_y"].value_counts().to_dict()
    weights = [1.0 / freq[y] for y in train_df["_y"]]
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, drop_last=False)
    val_dl   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, drop_last=False)
    test_dl  = DataLoader(test_ds,  batch_size=args.batch_size, shuffle=False, drop_last=False)

    # Gradient clipping
    def clip_gradients(model, max_norm=1.0):
        nn.utils.clip_grad_norm_(model.parameters(), max_norm)

    # Loop de treino
    for epoch in range(1, args.epochs + 1):
        # descongela embeddings após algumas épocas
        if epoch == (args.freeze_emb_first + 1):
            model.embedding.weight.requires_grad = True

        model.train()
        total_loss, total_correct, total_seen = 0.0, 0, 0
        for xb, yb in train_dl:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)

            

            loss.backward()
            clip_gradients(model)
            optimizer.step()

            total_loss   += float(loss.item()) * xb.size(0)
            total_correct += (out.argmax(1) == yb).sum().item()
            total_seen   += xb.size(0)

        tr_loss = total_loss / max(total_seen, 1)
        tr_acc  = total_correct / max(total_seen, 1)

        # Validação
        va_loss, va_acc, yv, pv = evaluate(
            model, val_dl, criterion, device, diag_first_batch=getattr(args, "diag_val_loss", False)
        )
        
        va_f1 = f1_score(yv, pv, average="macro", zero_division=0)


        scheduler.step(va_f1)

        print(f"Epoch {epoch:02d} | train_loss={tr_loss:.4f} acc={tr_acc:.4f} | "
              f"val_loss={va_loss:.4f} acc={va_acc:.4f} macroF1={va_f1:.4f}")

        if va_f1 > best_val_f1:
            best_val_f1, best_epoch, no_improve = va_f1, epoch, 0
            best_state = model.state_dict()
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"⏹️ Early stopping at epoch {epoch} (best F1={best_val_f1:.4f} @ epoch {best_epoch})")
                break

    # Restaura melhor estado e salva
    if best_state is not None:
        model.load_state_dict(best_state)
        torch.save(best_state, os.path.join(args.models_dir, "best_model.pt"))
        print(f"✅ Melhor modelo salvo: epoch={best_epoch} F1={best_val_f1:.4f}")

    # Teste
    print("== Avaliando no TEST ==")
    te_loss, te_acc, yt, pt = evaluate(model, test_dl, criterion, device)
    print(f"TEST: loss={te_loss:.4f} acc={te_acc:.4f}")

    # Report coerente apenas com classes presentes
    valid = unique_labels(yt, pt)
    valid_names = [le.classes_[i] for i in valid if i < len(le.classes_)]
    
    # ⚠️ Proteção contra predições vazias ou colapso de modelo
    if len(valid_names) == 0 or len(valid) == 0:
        print("⚠️ AVISO: Modelo gerou predições inválidas (todas as classes colapsadas).")
        print(f"   Unique labels em y_true: {np.unique(yt)}")
        print(f"   Unique labels em y_pred: {np.unique(pt)}")
        print(f"   valid_names vazio: {len(valid_names) == 0}")
        
        # Fallback: usar apenas classes que aparecem em y_true
        valid = np.unique(yt)
        valid_names = [le.classes_[i] for i in valid if i < len(le.classes_)]
        if len(valid_names) == 0:
            # Último recurso: reportar sem target_names
            print("   Usando fallback: relatório sem nomes de classes")
            rep = classification_report(yt, pt, digits=4, zero_division=0)
        else:
            rep = classification_report(yt, pt, labels=valid, target_names=valid_names, digits=4, zero_division=0)
    else:
        rep = classification_report(yt, pt, labels=valid, target_names=valid_names, digits=4, zero_division=0)
    
    print(rep)

    # Relatórios
    print("== Salvando artefatos ==")
    with open(os.path.join(out_reports, "classification_report.txt"), "w", encoding="utf-8") as f:
        f.write(rep)
    save_confusion_matrix(yt, pt, labels=le.classes_, out_csv=os.path.join(out_reports, "confusion_matrix.csv"))

    # Métricas por grupo (no test)
    test_pred_df = test_df[[args.grupo_col]].copy()
    test_pred_df["y_true"] = yt
    test_pred_df["y_pred"] = pt
    gm = group_metrics(test_pred_df, le, os.path.join(out_reports, "metrics_by_group.csv"))
    print("== Métricas por grupo (macro-F1 top) ==")
    print(gm.sort_values("macro_f1", ascending=False).head(10).to_string(index=False))

    # Salvar artefatos do modelo e config
    # w2v
    kv_path = os.path.join(args.models_dir, "w2v.kv")
    w2v.wv.save(kv_path)
    # vocab
    with open(os.path.join(args.models_dir, "vocab.pkl"), "wb") as f:
        pickle.dump(vocab, f)
    # label encoder
    with open(os.path.join(args.models_dir, "label_encoder.pkl"), "wb") as f:
        pickle.dump(le, f)
    # último estado
    torch.save(model.state_dict(), os.path.join(args.models_dir, "model.pt"))
    # config
    cfg = {
        "max_len": args.max_len,
        "hidden_dim": args.hidden_dim,
        "num_layers": args.num_layers,
        "dropout": args.dropout,
        "pad_idx": 0,
        "unk_idx": 1,
        "freeze_embeddings_at_infer": True,
        "tokenizer": "basic_tokenize_lower_ws",
        "cutoff": args.cutoff,
        "test_year": int(pd.to_datetime(args.cutoff).year) if args.cutoff else None,
        "embed_dim": args.embed_dim,
        "min_count": args.min_count,
        "w2v_min_count": args.w2v_min_count,
        "w2v_epochs": args.w2v_epochs,
    }
    with open(os.path.join(args.models_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print(f"✅ Finalizado. Artefatos em: {args.models_dir}")
    print(f"Relatórios em: {out_reports}")

if __name__ == "__main__":
    main()
