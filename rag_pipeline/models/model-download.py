import requests

url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
file_path = "mistral-7b-instruct-v0.1.Q4_K_M.gguf"

with requests.get(url, stream=True) as r:
    r.raise_for_status()
    with open(file_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

print("✅ Download complete.")
