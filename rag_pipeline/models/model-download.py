"""Download the Mistral-7B GGUF model for local inference."""

import os
from pathlib import Path

import requests
from tqdm import tqdm

MODEL_URL = (
    "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF"
    "/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
)
MODEL_DIR = Path(__file__).parent
MODEL_FILE = MODEL_DIR / "mistral-7b-instruct-v0.1.Q4_K_M.gguf"


def download_model():
    if MODEL_FILE.exists():
        size_gb = MODEL_FILE.stat().st_size / (1024**3)
        print(f"Model already exists at {MODEL_FILE} ({size_gb:.1f} GB). Skipping download.")
        return

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Mistral-7B GGUF to {MODEL_FILE} ...")

    response = requests.get(MODEL_URL, stream=True, timeout=30)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(MODEL_FILE, "wb") as f, tqdm(
        total=total_size, unit="B", unit_scale=True, desc="Downloading"
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))

    size_gb = MODEL_FILE.stat().st_size / (1024**3)
    print(f"Download complete: {MODEL_FILE} ({size_gb:.1f} GB)")


if __name__ == "__main__":
    download_model()
