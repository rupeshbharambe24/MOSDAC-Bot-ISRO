"""
MOSDAC Relationship Classifier - Training Script
Trains a BERT-based binary classifier to distinguish valid satellite-product
relationships from junk extracted by the pipeline.

Usage:
    python train_classifier.py
    python train_classifier.py --epochs 10 --batch_size 16
    python train_classifier.py --data training_data_curated.json --output models/mosdac_relation_classifier
"""

import json
import argparse
import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)


class RelationDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.encodings = tokenizer(
            texts, truncation=True, padding=True, max_length=max_length, return_tensors="pt"
        )
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


def load_curated_data(path):
    """Load training data from curated JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    examples = data["examples"]
    texts = [ex["text"] for ex in examples]
    labels = [ex["label"] for ex in examples]
    print(f"Loaded {len(texts)} examples ({sum(labels)} positive, {len(labels) - sum(labels)} negative)")
    return texts, labels


def compute_metrics(eval_pred):
    """Compute precision, recall, F1 for the Trainer."""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    tp = ((predictions == 1) & (labels == 1)).sum()
    fp = ((predictions == 1) & (labels == 0)).sum()
    fn = ((predictions == 0) & (labels == 1)).sum()
    tn = ((predictions == 0) & (labels == 0)).sum()
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(labels)
    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def train(args):
    print("=" * 60)
    print("MOSDAC Relationship Classifier - Training")
    print("=" * 60)

    # Load data
    texts, labels = load_curated_data(args.data)

    # Train/val split (80/20, stratified)
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"Train: {len(train_texts)} examples | Val: {len(val_texts)} examples")

    # Load tokenizer and model
    print(f"\nLoading base model: {args.base_model}")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.base_model, num_labels=2
    )

    # Create datasets
    train_dataset = RelationDataset(train_texts, train_labels, tokenizer)
    val_dataset = RelationDataset(val_texts, val_labels, tokenizer)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output + "_checkpoints",
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=2e-5,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_dir=args.output + "_logs",
        logging_steps=10,
        save_total_limit=3,
        seed=42,
        report_to="none",
    )

    # Trainer with early stopping
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    # Train
    print(f"\nTraining for up to {args.epochs} epochs (early stopping patience=3)...")
    print(f"Device: {training_args.device}")
    trainer.train()

    # Evaluate on validation set
    print("\n" + "=" * 60)
    print("Validation Results")
    print("=" * 60)
    results = trainer.evaluate()
    for key, value in results.items():
        if key.startswith("eval_"):
            print(f"  {key}: {value:.4f}")

    # Detailed classification report
    val_predictions = trainer.predict(val_dataset)
    preds = np.argmax(val_predictions.predictions, axis=-1)
    print("\nClassification Report:")
    print(classification_report(
        val_labels, preds,
        target_names=["INVALID (0)", "VALID (1)"]
    ))
    print("Confusion Matrix:")
    cm = confusion_matrix(val_labels, preds)
    print(f"  TN={cm[0][0]}  FP={cm[0][1]}")
    print(f"  FN={cm[1][0]}  TP={cm[1][1]}")

    # Save best model
    print(f"\nSaving model to {args.output}/")
    os.makedirs(args.output, exist_ok=True)
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)
    print("Done!")

    # Save training metadata
    meta = {
        "base_model": args.base_model,
        "training_data": args.data,
        "train_size": len(train_texts),
        "val_size": len(val_texts),
        "epochs_trained": int(trainer.state.epoch),
        "best_f1": results.get("eval_f1", 0),
        "best_accuracy": results.get("eval_accuracy", 0),
        "best_precision": results.get("eval_precision", 0),
        "best_recall": results.get("eval_recall", 0),
    }
    meta_path = os.path.join(args.output, "training_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Training metadata saved to {meta_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MOSDAC relationship classifier")
    parser.add_argument(
        "--data", default="training_data_curated.json",
        help="Path to curated training data JSON"
    )
    parser.add_argument(
        "--output", default="models/mosdac_relation_classifier",
        help="Output directory for trained model"
    )
    parser.add_argument(
        "--base_model", default="bert-base-uncased",
        help="Base model to fine-tune"
    )
    parser.add_argument("--epochs", type=int, default=15, help="Max training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    args = parser.parse_args()
    train(args)
