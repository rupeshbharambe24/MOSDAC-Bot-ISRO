with open('training_data.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Replace problematic characters
content = content.replace('�', '°')  # Degree symbol
content = content.replace('�', "'")  # Apostrophe

with open('training_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Encoding issues fixed in training_data.py")