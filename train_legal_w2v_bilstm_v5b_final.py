# -*- coding: utf-8 -*-
import os, re, json, argparse, random, pickle
from collections import defaultdict, Counter
from datetime import datetime

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_class_weight
from sklearn.utils.multiclass import unique_labels

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler

from gensim.models import Word2Vec

# --------------------------
# Utils & seed
# --------------------------
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def basic_tokenize_lower_ws(s):
    return re.findall(r"\w+|\S", str(s).lower())

# --------------------------
# Vocab / encoding helpers
# --------------------------
PAD, UNK = "<pad>", "<unk>"
PAD_IDX, UNK_IDX = 0, 1

def build_vocab(token_lists, min_count=1, max_size=None):
    freq = Counter(t for sent in token_lists for t in sent)
    items = [(t, c) for t, c in freq.items() if c >= min_count]
    items.sort(key=lambda x: (-x[1], x[0]))
    if max_size is not None:
        items = items[:max_size]
    itos = [PAD, UNK] + [t for t, _ in items]
    stoi = {t:i for i, t in enumerate(itos)}
    return stoi, itos

def encode_text(tokens, stoi, max_len):
    ids = [stoi.get(t, UNK_IDX) for t in tokens][:max_len]
    if len(ids) < max_len:
        ids += [PAD_IDX]*(max_len-len(ids))
    return np.array(ids, dtype=np.int64)

# --------------------------
# Dataset / Collate
# --------------------------
class TextClsDS(Dataset):
    def __init__(self, df, text_col, y_col, stoi, max_len, tokenize_fn):
        self.x = df[text_col].astype(str).tolist()
        self.y = df[y_col].astype(int).tolist()
        self.stoi = stoi
        self.max_len = max_len
        self.tok = tokenize_fn
    def __len__(self): return len(self.x)
    def __getitem__(self, i):
        tokens = self.tok(self.x[i])
        x_ids = encode_text(tokens, self.stoi, self.max_len)
        return torch.from_numpy(x_ids), torch.tensor(self.y[i], dtype=torch.long)

def collate_pad(batch):
    xs, ys = zip(*batch)
    return torch.stack(xs, 0), torch.stack(ys, 0)

# --------------------------
# Model
# --------------------------
class BiLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes,
                 pad_idx, w2v_weights=None, freeze_embeddings=True,
                 num_layers=1, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        if w2v_weights is not None:
            with torch.no_grad():
                self.embedding.weight[:w2v_weights.shape[0]].copy_(torch.tensor(w2v_weights))
        self.embedding.weight.requires_grad = not freeze_embeddings

        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=num_layers,
                            batch_first=True, bidirectional=True, dropout=dropout if num_layers > 1 else 0.0)
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim*2, num_classes)

    def forward(self, x):
        emb = self.embedding(x)                  # (B, T, E)
        out, _ = self.lstm(emb)                  # (B, T, 2H)
        h = out[:, -1, :]                        # last step pooling
        h = self.drop(h)
        return self.fc(h)                        # (B, C)

# --------------------------
# Evaluation / Reports
# --------------------------
@torch.no_grad()
def evaluate(model, dl, criterion, device, diag=False):
    model.eval()
    total_loss, total_correct, total_seen = 0.0, 0, 0
    all_y, all_pred = [], []
    for i, (xb, yb) in enumerate(dl):
        xb, yb = xb.to(device), yb.to(device)
        out = model(xb)
        loss = criterion(out, yb)
        if diag and i == 0:
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
    # salva contagens simples como CSV
    mat = defaultdict(lambda: defaultdict(int))
    for yt, yp in zip(y_true, y_pred):
        mat[int(yt)][int(yp)] += 1
    rows = []
    for yt in range(len(labels)):
        row = {'true': int(yt)}
        for yp in range(len(labels)):
            row[f'pred_{yp}'] = mat[yt][yp]
        rows.append(row)
    pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8")

def group_metrics(test_pred_df, le, out_csv):
    # calcula métricas por grupo simples (macro-avg dentro de cada grupo)
    res = []
    for g, sub in test_pred_df.groupby(test_pred_df.columns[0]):
        yt, yp = sub["y_true"].values, sub["y_pred"].values
        labs = unique_labels(yt, yp)
        f1 = f1_score(yt, yp, labels=labs, average="macro", zero_division=0)
        prec = f1_score(yt, yp, labels=labs, average="macro", zero_division=0)  # placeholder
        rec = f1_score(yt, yp, labels=labs, average="macro", zero_division=0)   # placeholder
        acc = (yt == yp).mean() if len(yt) else 0
        res.append(dict(grupo=g, macro_f1=f1, macro_precision=prec, macro_recall=rec, accuracy=acc))
    df = pd.DataFrame(res).sort_values("macro_f1", ascending=False)
    df.to_csv(out_csv, index=False, encoding="utf-8")
    return df

# --------------------------
# Main
# --------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--text-col", required=True)
    p.add_argument("--label-col", required=True)
    p.add_argument("--grupo-col", required=True)
    p.add_argument("--date-col", required=True)
    p.add_argument("--models-dir", required=True)

    p.add_argument("--max-len", type=int, default=256)
    p.add_argument("--embed-dim", type=int, default=200)
    p.add_argument("--hidden-dim", type=int, default=128)
    p.add_argument("--num-layers", type=int, default=1)
    p.add_argument("--dropout", type=float, default=0.2)
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--freeze-emb-first", type=int, default=2)

    p.add_argument("--w2v-min-count", type=int, default=5)
    p.add_argument("--w2v-epochs", type=int, default=5)
    p.add_argument("--min-train-per-class", type=int, default=0)   # collapse tail into __OTHER__ if >0
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--diag-val-loss", action="store_true")

    args = p.parse_args()
    os.makedirs(args.models_dir, exist_ok=True)
    out_reports = os.path.join(args.models_dir, "reports")
    os.makedirs(out_reports, exist_ok=True)

    set_seed(args.seed)

    print("== Carregando dataset ==")
    df = pd.read_csv(args.data, encoding="utf-8")
    # sanity
    df = df.dropna(subset=[args.text_col, args.label_col, args.grupo_col, args.date_col])
    df[args.text_col] = df[args.text_col].astype(str)

    # ---------------------- temporal split ----------------------
    print("== Split temporal ==")
    # Assume que date_col é YYYY-MM-DD ou compatível com pandas
    df[args.date_col] = pd.to_datetime(df[args.date_col], errors="coerce")
    df = df.dropna(subset=[args.date_col])
    df = df.sort_values(args.date_col)

    # 80% trainval, 20% test por tempo
    cut = int(len(df) * 0.8)
    base_df = df.iloc[:cut].copy()
    test_df = df.iloc[cut:].copy()

    # ---------------------- collapse tail (opcional) ----------------------
    if args.min_train_per_class and args.min_train_per_class > 0:
        # colapsa rótulos com < min_train_per_class para __OTHER__ (na base de treino/val)
        cnt = base_df[args.label_col].value_counts()
        tail = set(cnt[cnt < args.min_train_per_class].index)
        if len(tail) > 0:
            print(f"⚙️  Collapsing {len(tail)} tail classes (<{args.min_train_per_class} samples) into __OTHER__")
            base_df[args.label_col] = base_df[args.label_col].apply(lambda x: "__OTHER__" if x in tail else x)

    # ---------------------- LabelEncoder fit no conjunto base ----------------------
    le = LabelEncoder()
    le.fit(base_df[args.label_col].values.tolist() + test_df[args.label_col].values.tolist())
    base_df["_y"] = le.transform(base_df[args.label_col])
    test_df["_y"] = le.transform(test_df[args.label_col])

    # ---------------------- stratified split robust to rare ----------------------
    print("== Train/Val estratificado com tratamento de classes raras ==")
    yb = base_df["_y"].values
    # classes com <2 amostras serão forçadas ao TRAIN
    vc = base_df["_y"].value_counts()
    rare_ids = set(vc[vc < 2].index.tolist())
    n_rare = int((base_df["_y"].isin(rare_ids)).sum())
    if n_rare > 0:
        print(f"⚠️ {n_rare} linhas de {len(rare_ids)} classes têm <2 amostras; elas irão apenas para TRAIN (não entram na validação).")

    base_df["_is_rare"] = base_df["_y"].isin(rare_ids)
    base_common = base_df[~base_df["_is_rare"]]
    base_rare   = base_df[ base_df["_is_rare"]]

    if len(base_common) > 0:
        train_common, val_common = train_test_split(
            base_common, test_size=0.10, random_state=args.seed, stratify=base_common["_y"]
        )
        train_df = pd.concat([train_common, base_rare], axis=0).sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
        val_df   = val_common.reset_index(drop=True)
    else:
        # tudo é raro? joga 10% pra val sem estratify
        train_df, val_df = train_test_split(base_df, test_size=0.10, random_state=args.seed)

    print("== Preparando conjunto de teste ==")
    print(f"Train: {len(train_df)} | Val: {len(val_df)} | (rare_in_train={(train_df['_is_rare']).sum()})")

    # ---------------------- Tokenization ----------------------
    print("== Treinando Word2Vec e vocabulário ==")
    train_tokens = [basic_tokenize_lower_ws(t) for t in train_df[args.text_col].astype(str)]
    val_tokens   = [basic_tokenize_lower_ws(t) for t in val_df[args.text_col].astype(str)]
    test_tokens  = [basic_tokenize_lower_ws(t) for t in test_df[args.text_col].astype(str)]

    w2v = Word2Vec(
        sentences=train_tokens,
        vector_size=args.embed_dim,
        window=5,
        min_count=args.w2v_min_count,
        workers=1,
        epochs=args.w2v_epochs,
        sg=1
    )
    kv = w2v.wv

    # vocab
    stoi, itos = build_vocab(train_tokens, min_count=1)
    vocab = stoi
    # w2v weights (for known words)
    w2v_weights = np.random.normal(scale=0.6, size=(len(vocab), args.embed_dim)).astype(np.float32)
    for t, idx in vocab.items():
        if t in kv:
            w2v_weights[idx] = kv[t]

    # encode datasets
    train_ds = TextClsDS(train_df, args.text_col, "_y", vocab, args.max_len, basic_tokenize_lower_ws)
    val_ds   = TextClsDS(val_df,   args.text_col, "_y", vocab, args.max_len, basic_tokenize_lower_ws)
    test_ds  = TextClsDS(test_df,  args.text_col, "_y", vocab, args.max_len, basic_tokenize_lower_ws)

    # ---------------------- class weights ----------------------
    print("== Calculando class weights ==")
    classes = np.unique(train_df["_y"].values)
    cw = compute_class_weight(class_weight="balanced", classes=classes, y=train_df["_y"].values)
    full = np.ones(len(le.classes_), dtype=np.float32)
    for c, w in zip(classes, cw):
        full[int(c)] = float(w)
    w = torch.tensor(full, dtype=torch.float)
    w = w * (len(w) / w.sum())
    w = torch.clamp(w, max=5.0)
    class_weights = w

    # ---------------------- model/optim/loss/sched ----------------------
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
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
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device), label_smoothing=0.1)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=1)

    # ---------------------- sampler (oversampling raras) ----------------------
    freq = train_df["_y"].value_counts().to_dict()
    weights = [1.0 / freq[y] for y in train_df["_y"]]
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

    train_dl = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, drop_last=False)
    val_dl   = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, drop_last=False)
    test_dl  = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, drop_last=False)

    print("== Treinando ==")
    best_val_f1, best_epoch, patience, no_improve = 0.0, 0, 2, 0
    best_state = None

    for epoch in range(1, args.epochs + 1):
        # unfreeze embeddings after N epochs
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
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += float(loss.item()) * xb.size(0)
            total_correct += (out.argmax(1) == yb).sum().item()
            total_seen += xb.size(0)
        tr_loss = total_loss / max(total_seen, 1)
        tr_acc  = total_correct / max(total_seen, 1)

        # validation
        va_loss, va_acc, all_y, all_p = evaluate(model, val_dl, criterion, device, diag=args.diag_val_loss)
        va_f1 = f1_score(all_y, all_p, average="macro", zero_division=0)
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

    # load best & save
    if best_state is not None:
        model.load_state_dict(best_state)
        torch.save(best_state, os.path.join(args.models_dir, "best_model.pt"))
        print(f"✅ Melhor modelo salvo: epoch={best_epoch} F1={best_val_f1:.4f}")

    # ---------------------- final test ----------------------
    print("== Avaliando no TEST ==")
    te_loss, te_acc, yt, pt = evaluate(model, test_dl, criterion, device)
    print(f"TEST: loss={te_loss:.4f} acc={te_acc:.4f}")

    valid = unique_labels(yt, pt)
    valid_names = [le.classes_[i] for i in valid if i < len(le.classes_)]
    rep = classification_report(yt, pt, labels=valid, target_names=valid_names, digits=4, zero_division=0)
    print(rep)

    # reports
    os.makedirs(out_reports, exist_ok=True)
    with open(os.path.join(out_reports, "classification_report.txt"), "w", encoding="utf-8") as f:
        f.write(rep)
    save_confusion_matrix(yt, pt, labels=le.classes_, out_csv=os.path.join(out_reports, "confusion_matrix.csv"))

    # group metrics
    test_pred_df = test_df[[args.grupo_col]].copy()
    test_pred_df["y_true"] = yt
    test_pred_df["y_pred"] = pt
    gm = group_metrics(test_pred_df, le, os.path.join(out_reports, "metrics_by_group.csv"))
    print("== Métricas por grupo (macro-F1 top) ==")
    print(gm.head(10).to_string(index=False))

    # artifacts
    print("== Salvando artefatos ==")
    kv_path = os.path.join(args.models_dir, "w2v.kv")
    w2v.wv.save(kv_path)
    with open(os.path.join(args.models_dir, "vocab.pkl"), "wb") as f:
        pickle.dump(vocab, f)
    with open(os.path.join(args.models_dir, "label_encoder.pkl"), "wb") as f:
        pickle.dump(le, f)
    torch.save(model.state_dict(), os.path.join(args.models_dir, "model.pt"))
    cfg = {
        "max_len": args.max_len,
        "hidden_dim": args.hidden_dim,
        "num_layers": args.num_layers,
        "dropout": args.dropout,
        "pad_idx": PAD_IDX,
        "unk_idx": UNK_IDX,
        "freeze_embeddings_at_infer": True,
        "tokenizer": "basic_tokenize_lower_ws",
        "embed_dim": args.embed_dim,
        "w2v_min_count": args.w2v_min_count,
        "w2v_epochs": args.w2v_epochs,
        "min_train_per_class": args.min_train_per_class,
    }
    with open(os.path.join(args.models_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print(f"✅ Finalizado. Artefatos em: {args.models_dir}")
    print(f"Relatórios em: {out_reports}")

if __name__ == "__main__":
    main()
