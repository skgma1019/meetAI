"""Train a softmax classifier on nonverbal features and save as JSON checkpoint."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.analyzers.nonverbal.classifier import LABELS
from app.analyzers.nonverbal.extractor import FEATURE_NAMES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train softmax classifier for nonverbal behavior.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=REPO_ROOT / "data" / "processed" / "nonverbal_features.csv",
    )
    parser.add_argument(
        "--output-model",
        type=Path,
        default=REPO_ROOT / "outputs" / "checkpoints" / "nonverbal_classifier.json",
    )
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--l2-penalty", type=float, default=1e-4)
    return parser.parse_args()


def load_data(path: Path) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    train_rows = [r for r in rows if r["split"] == "train"]
    val_rows = [r for r in rows if r["split"] == "validation"]

    label_to_idx = {label: i for i, label in enumerate(LABELS)}

    def to_arrays(data: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        X = np.array([[float(r[f]) for f in FEATURE_NAMES] for r in data], dtype=np.float64)
        y = np.array([label_to_idx[r["label"]] for r in data], dtype=np.int32)
        return X, y

    X_train, y_train = to_arrays(train_rows)
    X_val, y_val = to_arrays(val_rows)
    return X_train, y_train, X_val, y_val


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp_l = np.exp(shifted)
    return exp_l / exp_l.sum(axis=1, keepdims=True)


def cross_entropy_loss(probs: np.ndarray, y: np.ndarray) -> float:
    n = len(y)
    correct_probs = probs[np.arange(n), y]
    return -np.mean(np.log(correct_probs + 1e-12))


def accuracy(probs: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(probs.argmax(axis=1) == y))


def train(
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    n_classes: int,
    epochs: int,
    lr: float,
    batch_size: int,
    l2: float,
) -> tuple[np.ndarray, np.ndarray]:
    n_features = X_train.shape[1]
    W = np.zeros((n_classes, n_features), dtype=np.float64)
    b = np.zeros(n_classes, dtype=np.float64)
    n = len(y_train)

    for epoch in range(epochs):
        perm = np.random.permutation(n)
        X_shuf, y_shuf = X_train[perm], y_train[perm]

        for start in range(0, n, batch_size):
            Xb = X_shuf[start : start + batch_size]
            yb = y_shuf[start : start + batch_size]
            nb = len(yb)

            logits = Xb @ W.T + b          # (nb, n_classes)
            probs = softmax(logits)

            # gradient of cross-entropy wrt logits
            delta = probs.copy()
            delta[np.arange(nb), yb] -= 1
            delta /= nb

            dW = delta.T @ Xb + l2 * W     # (n_classes, n_features)
            db = delta.sum(axis=0)          # (n_classes,)

            W -= lr * dW
            b -= lr * db

        if (epoch + 1) % 50 == 0:
            logits = X_train @ W.T + b
            probs = softmax(logits)
            loss = cross_entropy_loss(probs, y_train)
            acc = accuracy(probs, y_train)
            print(f"  epoch {epoch+1:4d} | loss {loss:.4f} | train_acc {acc:.4f}")

    return W, b


def main() -> None:
    args = parse_args()

    print(f"Loading features from {args.input_csv}")
    X_train, y_train, X_val, y_val = load_data(args.input_csv)
    print(f"Train: {len(X_train)}, Val: {len(X_val)}")

    # z-score normalization using train statistics
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0)
    std[std == 0] = 1.0
    X_train_norm = (X_train - mean) / std
    X_val_norm = (X_val - mean) / std

    print(f"Training softmax classifier ({args.epochs} epochs)...")
    np.random.seed(42)
    W, b = train(
        X_train_norm,
        y_train,
        n_classes=len(LABELS),
        epochs=args.epochs,
        lr=args.learning_rate,
        batch_size=args.batch_size,
        l2=args.l2_penalty,
    )

    train_probs = softmax(X_train_norm @ W.T + b)
    val_probs = softmax(X_val_norm @ W.T + b)
    train_acc = accuracy(train_probs, y_train)
    val_acc = accuracy(val_probs, y_val)
    train_loss = cross_entropy_loss(train_probs, y_train)
    val_loss = cross_entropy_loss(val_probs, y_val)

    # Per-class accuracy on validation
    per_class: dict[str, float] = {}
    for i, label in enumerate(LABELS):
        mask = y_val == i
        if mask.sum() > 0:
            per_class[label] = float((val_probs[mask].argmax(axis=1) == i).mean())

    print(f"\nTrain acc: {train_acc:.4f}  Val acc: {val_acc:.4f}")
    print(f"Train loss: {train_loss:.4f}  Val loss: {val_loss:.4f}")
    print("Per-class val accuracy:")
    for label, acc_val in per_class.items():
        print(f"  {label}: {acc_val:.4f}")

    feature_stats = {
        name: {"mean": float(mean[i]), "std": float(std[i])}
        for i, name in enumerate(FEATURE_NAMES)
    }

    payload = {
        "feature_names": FEATURE_NAMES,
        "feature_stats": feature_stats,
        "labels": LABELS,
        "weights": W.tolist(),
        "biases": b.tolist(),
        "metrics": {
            "train_count": int(len(X_train)),
            "val_count": int(len(X_val)),
            "train_accuracy": round(train_acc, 6),
            "val_accuracy": round(val_acc, 6),
            "train_loss": round(train_loss, 6),
            "val_loss": round(val_loss, 6),
            "val_accuracy_per_class": {k: round(v, 6) for k, v in per_class.items()},
        },
    }

    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    args.output_model.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved checkpoint to {args.output_model}")


if __name__ == "__main__":
    main()
