# -*- coding: utf-8 -*-
import os, re, json, math, argparse, random, pickle, csv
from datetime import datetime
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from gensim.models import Word2Vec, KeyedVectors

# --------------------------
# Utils e seed
# --------------------------
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

# --------------------------
# Tokenização / normalização
# --------------------------
def basic_tokenize(text: str):
    # simples, rápida e robusta. Ajuste aqui para refletir o que você quiser (e depois replique no model_server.py).
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text.split()

# --------------------------
# Dataset e DataLoader
# --------------------------
class TextDataset(Dataset):
    def __init__(self, df, text_col, y_idx, vocab, max_len=400, pad_idx=0, unk_idx=1):
        self.texts = df[text_col].astype(str).tolist()
        self.y = df[y_idx].astype(int).tolist()
        self.vocab = vocab
        self.max_len = max_len
        self.pad_idx = pad_idx
        self.unk_idx = unk_idx

    def __len__(self):
        return len(self.texts)

    def encode(self, text):
        toks = basic_tokenize(text)
        ids = [ self.vocab.get(t, self.unk_idx) for t in toks ]
        ids = ids[:self.max_len]
        if len(ids) < self.max_len:
            ids += [self.pad_idx] * (self.max_len - len(ids))
        return ids

    def __getitem__(self, i):
        ids = self.encode(self.texts[i])
        return torch.tensor(ids, dtype=torch.long), torch.tensor(self.y[i], dtype=torch.long)

# --------------------------
# Modelo BiLSTM
# --------------------------
class BiLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, pad_idx=0,
                 w2v_weights=None, freeze_embeddings=False, num_layers=1, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        if w2v_weights is not None:
            self.embedding.weight.data.copy_(torch.from_numpy(w2v_weights))
        self.embedding.weight.requires_grad = not freeze_embeddings
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=True,
                            num_layers=num_layers, dropout=dropout if num_layers > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x):
        emb = self.embedding(x)        # (B,T,E)
        out, _ = self.lstm(emb)        # (B,T,2H)
        out = self.dropout(out)
        out, _ = torch.max(out, dim=1) # (B,2H)
        return self.fc(out)            # (B,C)


# --------------------------
# Treino / Avaliação
# --------------------------
def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss, total, correct = 0.0, 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        logits = model(xb)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()

        total_loss += float(loss.item()) * yb.size(0)
        pred = logits.argmax(dim=-1)
        correct += (pred == yb).sum().item()
        total += yb.size(0)
    return total_loss / max(total,1), correct / max(total,1)

@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, total, correct = 0.0, 0, 0
    all_y, all_pred = [], []
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        logits = model(xb)
        loss = criterion(logits, yb)
        total_loss += float(loss.item()) * yb.size(0)
        pred = logits.argmax(dim=-1)
        correct += (pred == yb).sum().item()
        total += yb.size(0)
        all_y.extend(yb.cpu().numpy().tolist())
        all_pred.extend(pred.cpu().numpy().tolist())
    return total_loss / max(total,1), correct / max(total,1), np.array(all_y), np.array(all_pred)

# --------------------------
# Word2Vec + Vocabulário
# --------------------------
def build_w2v_and_vocab(texts, embed_dim=200, window=5, min_count=3, workers=4, sg=1, epochs=10, specials=("<pad>", "<unk>")):
    sentences = [basic_tokenize(t) for t in texts]
    w2v = Word2Vec(sentences=sentences, vector_size=embed_dim, window=window, min_count=min_count,
                   workers=workers, sg=sg, epochs=epochs)
    kv = w2v.wv
    # vocab: especiais + palavras
    vocab = {specials[0]:0, specials[1]:1}
    for i, tok in enumerate(kv.index_to_key):
        vocab[tok] = i + len(specials)
    # matriz de pesos
    vocab_size = len(vocab)
    weights = np.random.normal(0,0.1,size=(vocab_size, embed_dim)).astype(np.float32)
    # preenche com vetores conhecidos
    for tok, idx in vocab.items():
        if tok in kv:
            weights[idx] = kv[tok]
    return w2v, kv, vocab, weights

# --------------------------
# Split temporal
# --------------------------
def temporal_split(df, date_col="data_decisao", cutoff="2024-12-31", test_year="2025"):
    # Mantemos: train+val <= cutoff; test = ano=test_year (se existir)
    df = df.copy()
    # parse
    def parse_date(x):
        # espera formatos como YYYY-MM-DD ou YYYYMMDD ou DD/MM/YYYY
        x = str(x or "").strip()
        for fmt in ("%Y-%m-%d","%Y%m%d","%d/%m/%Y"):
            try: return datetime.strptime(x, fmt)
            except Exception: pass
        return None
    dt = df[date_col].apply(parse_date)
    df["_dt"] = dt
    # condições
    cutoff_dt = datetime.strptime(cutoff, "%Y-%m-%d")
    trainval_mask = (df["_dt"].notna()) & (df["_dt"] <= cutoff_dt)
    test_mask = (df["_dt"].notna()) & (df["_dt"].dt.strftime("%Y") == str(test_year))
    # fallback: se test ficar vazio, faz split aleatório 90/10
    if df[test_mask].empty:
        perm = np.random.permutation(len(df))
        test_sz = max(1, int(0.1 * len(df)))
        test_idx = set(perm[:test_sz])
        df["_split"] = ["test" if i in test_idx else "trainval" for i in range(len(df))]
    else:
        df["_split"] = np.where(test_mask, "test", np.where(trainval_mask, "trainval", "drop"))
    # drop linhas sem data válida (ou pós cutoff fora do test_year)
    kept = df[df["_split"] != "drop"].copy()
    return kept

# --------------------------
# Métricas e relatórios
# --------------------------
def save_confusion_matrix(y_true, y_pred, labels, out_csv):
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(labels))))
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([""] + list(labels))
        for i, row in enumerate(cm):
            w.writerow([labels[i]] + list(row))

def group_metrics(df_true_pred, label_encoder, out_csv):
    # df_true_pred: colunas ['grupo', 'y_true', 'y_pred']
    rows = []
    for g, sub in df_true_pred.groupby("grupo"):
        y_true = sub["y_true"].to_numpy()
        y_pred = sub["y_pred"].to_numpy()
        rep = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        rows.append([g, rep["macro avg"]["f1-score"], rep["macro avg"]["precision"],
                     rep["macro avg"]["recall"], rep["accuracy"]])
    out = pd.DataFrame(rows, columns=["grupo","macro_f1","macro_precision","macro_recall","accuracy"])
    out.sort_values("macro_f1", ascending=False, inplace=True)
    out.to_csv(out_csv, index=False, encoding="utf-8")
    return out

# --------------------------
# Main
# --------------------------

def main():

    import numpy as np  # garante o alias no escopo local
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/interim/corpus_geral.csv", help="CSV com colunas: text,label,grupo,data_decisao, ...")
    ap.add_argument("--text-col", default="text")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--grupo-col", default="grupo")
    ap.add_argument("--date-col", default="data_decisao")
    ap.add_argument("--models-dir", default="models/legal_bilstm")
    ap.add_argument("--reports-subdir", default="reports")
    ap.add_argument("--cutoff", default="2024-12-31", help="Treino/val <= cutoff")
    ap.add_argument("--test-year", default="2025", help="Teste = ano 'YYYY'")
    ap.add_argument("--max-len", type=int, default=400)
    ap.add_argument("--embed-dim", type=int, default=200)
    ap.add_argument("--hidden-dim", type=int, default=128)
    ap.add_argument("--num-layers", type=int, default=1)
    ap.add_argument("--dropout", type=float, default=0.2)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--min-count", type=int, default=3, help="min_count do Word2Vec")
    ap.add_argument("--w2v-epochs", type=int, default=10)
    ap.add_argument("--freeze-emb-first", type=int, default=2, help="épocas iniciais com embeddings congelados")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    set_seed(args.seed)
    os.makedirs(args.models_dir, exist_ok=True)
    out_reports = os.path.join(args.models_dir, args.reports_subdir)
    os.makedirs(out_reports, exist_ok=True)

    print("== Carregando dataset ==")
    df = pd.read_csv(args.data)
    # sanity: drop linhas vazias
    df = df.dropna(subset=[args.text_col, args.label_col])
    df[args.text_col] = df[args.text_col].astype(str).str.strip()
    df = df[df[args.text_col].str.len() > 0].copy()

    # Split temporal
    print("== Split temporal ==")
    kept = temporal_split(df, date_col=args.date_col, cutoff=args.cutoff, test_year=args.test_year)
    trainval = kept[kept["_split"]=="trainval"].copy()
    test = kept[kept["_split"]=="test"].copy()
    if test.empty:
        # fallback já tratado em temporal_split; aqui só garantimos colunas
        test = kept[kept["_split"]=="test"].copy()

    # Label encoding
    le = LabelEncoder()
    y_trainval = le.fit_transform(trainval[args.label_col].astype(str).values)
    trainval = trainval.assign(_y=y_trainval)

    print("== Train/Val estratificado com tratamento de classes raras ==")
    from sklearn.model_selection import StratifiedShuffleSplit

    # 1) separar classes raras (<2) para não irem à validação
    vc = trainval["_y"].value_counts()
    rare_labels = set(vc[vc < 2].index.tolist())
    rare_df  = trainval[trainval["_y"].isin(rare_labels)].copy()
    base_df  = trainval[~trainval["_y"].isin(rare_labels)].copy()

    # 2) tenta estratificar só no base_df
    def random_split(df_in, test_size=0.1, seed=42):
        rs = np.random.RandomState(seed)
        idx = np.arange(len(df_in))
        rs.shuffle(idx)
        n_val = max(1, int(test_size * len(df_in)))
        va_idx = set(idx[:n_val])
        tr_idx = [i for i in idx if i not in va_idx]
        return df_in.iloc[tr_idx].copy(), df_in.iloc[list(va_idx)].copy()

    train_df = None
    val_df   = None

    # Garantir que o conjunto de teste tenha as mesmas classes codificadas
    print("== Preparando conjunto de teste ==")
    valid_labels = set(le.classes_)
    test = test[test[args.label_col].isin(valid_labels)].copy()
    test["_y"] = le.transform(test[args.label_col].astype(str).values)


    if len(base_df) >= 2 and base_df["_y"].nunique() >= 2:
        sss = StratifiedShuffleSplit(n_splits=1, test_size=0.1, random_state=args.seed)
        idx = np.arange(len(base_df))
        for tr_idx, va_idx in sss.split(idx, base_df["_y"].to_numpy()):
            base_train = base_df.iloc[tr_idx].copy()
            base_val   = base_df.iloc[va_idx].copy()
        # classes raras vão só para treino
        train_df = pd.concat([base_train, rare_df], ignore_index=True)
        val_df   = base_val
    else:
        # fallback: split aleatório no trainval inteiro
        print("[WARN] Poucos dados/classes para estratificar; usando split aleatório 90/10.")
        train_df, val_df = random_split(trainval, test_size=0.1, seed=args.seed)

    print(f"Train: {len(train_df)} | Val: {len(val_df)} | (rare_in_train={len(rare_df)})")

    # Word2Vec + Vocab
    print("== Treinando Word2Vec e vocabulário ==")
    w2v, kv, vocab, w2v_weights = build_w2v_and_vocab(
        texts=train_df[args.text_col].tolist(),
        embed_dim=args.embed_dim,
        window=5,
        min_count=args.min_count,
        workers=os.cpu_count() or 4,
        sg=1,
        epochs=args.w2v_epochs
    )

    # Datasets
    PAD_IDX, UNK_IDX = 0, 1
    train_ds = TextDataset(train_df, args.text_col, "_y", vocab, max_len=args.max_len, pad_idx=PAD_IDX, unk_idx=UNK_IDX)
    val_ds   = TextDataset(val_df,   args.text_col, "_y", vocab, max_len=args.max_len, pad_idx=PAD_IDX, unk_idx=UNK_IDX)
    test_ds  = TextDataset(test,     args.text_col, "_y", vocab, max_len=args.max_len, pad_idx=PAD_IDX, unk_idx=UNK_IDX)

    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, drop_last=False)
    val_dl   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, drop_last=False)
    test_dl  = DataLoader(test_ds,  batch_size=args.batch_size, shuffle=False, drop_last=False)

    # Class weights (balanceado)
    print("== Calculando class weights ==")
    cw = compute_class_weight(class_weight="balanced", classes=np.arange(len(le.classes_)), y=train_df["_y"].to_numpy())
    class_weights = torch.tensor(cw, dtype=torch.float32)

    # Modelo
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = BiLSTMClassifier(
        vocab_size=len(vocab),
        embed_dim=args.embed_dim,
        hidden_dim=args.hidden_dim,
        num_classes=len(le.classes_),
        pad_idx=PAD_IDX,
        w2v_weights=w2v_weights,
        freeze_embeddings=True,  # começa congelado
        num_layers=args.num_layers,
        dropout=args.dropout
    ).to(device)

    # === modelo já criado acima ===
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    print("== Treinando ==")

    # ============================================
    # 🧩 TRAINING STABILITY PACK v1.1
    # ============================================

    # (1) Focal Loss opcional — melhora classes raras
    class FocalLoss(nn.Module):
        def __init__(self, weight=None, gamma=2.0):
            super().__init__()
            self.gamma = gamma
            self.weight = weight
            self.ce = nn.CrossEntropyLoss(weight=weight)
        def forward(self, logits, target):
            logpt = -self.ce(logits, target)   # log p_t
            pt = torch.exp(logpt)              # p_t
            return ((1 - pt) ** self.gamma * -logpt).mean()

    # Use Focal Loss se habilitado; caso contrário, CE balanceada
    USE_FOCAL = False
    # ======== LOSS & SCHEDULER (stable) ========
    # CrossEntropy com label smoothing ajuda em 486 classes
    criterion = nn.CrossEntropyLoss(
        weight=class_weights.to(device),
        label_smoothing=0.1  # requer PyTorch >= 1.10 (você está em 2.9)
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=1
    )



    # (3) Early stopping baseado no F1 de validação
    best_val_f1, best_epoch, patience, no_improve = 0.0, 0, 3, 0
    best_state = None

    # (4) Oversampling — aumenta presença das classes raras no treino
    from torch.utils.data import WeightedRandomSampler
    freq = train_df["_y"].value_counts().to_dict()
    weights = [1.0 / freq[y] for y in train_df["_y"]]
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)
    # train_dl = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, drop_last=False)
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, drop_last=False)


    # (5) Gradient clipping para LSTM
    def clip_gradients(model, max_norm=1.0):
        nn.utils.clip_grad_norm_(model.parameters(), max_norm)

    # --------------------------------------------
    # 🔁 LOOP DE TREINAMENTO
    # --------------------------------------------
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
            clip_gradients(model)  # evita gradientes explosivos
            optimizer.step()

            total_loss   += float(loss.item()) * xb.size(0)
            total_correct += (out.argmax(1) == yb).sum().item()
            total_seen   += xb.size(0)

        tr_loss = total_loss / max(total_seen, 1)
        tr_acc  = total_correct / max(total_seen, 1)

        # --- Validação ---
        model.eval()
        all_y, all_p = [], []
        va_loss, va_correct, va_seen = 0.0, 0, 0
        with torch.no_grad():
            for xb, yb in val_dl:
                xb, yb = xb.to(device), yb.to(device)
                out  = model(xb)
                loss = criterion(out, yb)
                va_loss   += float(loss.item()) * xb.size(0)
                va_correct += (out.argmax(1) == yb).sum().item()
                va_seen   += xb.size(0)
                all_y.extend(yb.cpu().numpy())
                all_p.extend(out.argmax(1).cpu().numpy())

        from sklearn.metrics import f1_score
        va_loss /= max(va_seen, 1)
        va_acc   = va_correct / max(va_seen, 1)
        va_f1    = f1_score(all_y, all_p, average="macro", zero_division=0)

        scheduler.step(va_f1)  # ajusta LR

        print(f"Epoch {epoch:02d} | train_loss={tr_loss:.4f} acc={tr_acc:.4f} | "
              f"val_loss={va_loss:.4f} acc={va_acc:.4f} macroF1={va_f1:.4f}")

        # Early stopping + best checkpoint
        if va_f1 > best_val_f1:
            best_val_f1, best_epoch, no_improve = va_f1, epoch, 0
            best_state = model.state_dict()
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"⏹️ Early stopping at epoch {epoch} (best F1={best_val_f1:.4f} @ epoch {best_epoch})")
                break

    # usa melhor estado
    if best_state is not None:
        model.load_state_dict(best_state)
        # também salva como best_model.pt
        torch.save(best_state, os.path.join(args.models_dir, "best_model.pt"))
        print(f"✅ Melhor modelo salvo: epoch={best_epoch} F1={best_val_f1:.4f}")

    # --------------------------------------------
    # 🧪 Teste final
    # --------------------------------------------
    print("== Avaliando no TEST ==")
    te_loss, te_acc, yt, pt = evaluate(model, test_dl, criterion, device)
    print(f"TEST: loss={te_loss:.4f} acc={te_acc:.4f}")

    # Relatório coerente apenas com classes presentes
    from sklearn.metrics import classification_report
    import numpy as np
    from sklearn.utils.multiclass import unique_labels
    valid = unique_labels(yt, pt)
    valid_names = [le.classes_[i] for i in valid if i < len(le.classes_)]
    rep = classification_report(yt, pt, labels=valid, target_names=valid_names, digits=4, zero_division=0)
    print(rep)

    # --------------------------------------------
    # 📊 Relatórios
    # --------------------------------------------
    with open(os.path.join(out_reports, "classification_report.txt"), "w", encoding="utf-8") as f:
        f.write(rep)

    save_confusion_matrix(yt, pt, labels=le.classes_, out_csv=os.path.join(out_reports, "confusion_matrix.csv"))

    # Métricas por grupo (no test)
    test_pred_df = test[[args.grupo_col]].copy()
    test_pred_df["y_true"] = yt
    test_pred_df["y_pred"] = pt
    gm = group_metrics(test_pred_df, le, os.path.join(out_reports, "metrics_by_group.csv"))
    print("== Métricas por grupo (macro-F1 top) ==")
    print(gm.head(10).to_string(index=False))

    # --------------------------------------------
    # 💾 Salvar artefatos do modelo
    # --------------------------------------------
    print("== Salvando artefatos ==")
    # w2v
    kv_path = os.path.join(args.models_dir, "w2v.kv")
    w2v.wv.save(kv_path)
    # vocab
    with open(os.path.join(args.models_dir, "vocab.pkl"), "wb") as f:
        pickle.dump(vocab, f)
    # label encoder
    with open(os.path.join(args.models_dir, "label_encoder.pkl"), "wb") as f:
        pickle.dump(le, f)
    # model (último estado treinado)
    torch.save(model.state_dict(), os.path.join(args.models_dir, "model.pt"))
    # config
    cfg = {
        "max_len": args.max_len,
        "hidden_dim": args.hidden_dim,
        "num_layers": args.num_layers,
        "dropout": args.dropout,
        "pad_idx": 0,
        "unk_idx": 1,
        "freeze_embeddings_at_infer": True,  # manter congelado no server
        "tokenizer": "basic_tokenize_lower_ws",
        "cutoff": args.cutoff,
        "test_year": args.test_year,
        "embed_dim": args.embed_dim,
        "min_count": args.min_count,
        "w2v_epochs": args.w2v_epochs,
    }
    with open(os.path.join(args.models_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print(f"✅ Finalizado. Artefatos em: {args.models_dir}")
    print(f"Relatórios em: {out_reports}")

if __name__ == "__main__":
    main()
