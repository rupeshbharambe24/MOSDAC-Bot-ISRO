from setuptools import setup, find_packages

setup(
    name="satsage",
    version="0.1.0",
    description="AI-powered satellite data query assistant for ISRO's MOSDAC portal",
    author="Rupesh Bharambe",
    url="https://github.com/rupeshbharambe24/SatSage",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        # NLP
        "spacy>=3.7.0",
        "transformers>=4.37.0",
        "torch>=2.1.0",
        "sentence-transformers>=2.2.2",
        # Knowledge Graph
        "py2neo>=2021.2.4",
        "neo4j>=5.12.0",
        # Vector Store
        "faiss-cpu>=1.7.4",
        # LLM
        "llama-cpp-python>=0.2.55",
        # Data Collection
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "tldextract>=3.4.0",
        "pdfplumber>=0.10.0",
        "PyPDF2>=3.0.0",
        "pdfminer.six>=20221105",
        "python-docx>=0.8.11",
        "pdf2image>=1.16.0",
        "pytesseract>=0.3.10",
        "pillow>=10.1.0",
        "opencv-python-headless>=4.9.0",
        # Utilities
        "numpy>=1.26.0",
        "pandas>=2.0.0",
        "tqdm>=4.66.0",
        "geopy>=2.4.0",
        "langdetect>=1.0.9",
        "indic-transliteration>=2.3.36",
    ],
)
