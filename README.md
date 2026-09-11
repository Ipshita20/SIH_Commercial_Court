# NyayaLens — Commercial Court Intelligence

AI-assisted legal research PoC/MVP for Commercial Courts.

## What it does
- Legal query search over the bundled Commercial Courts knowledge base
- Explainable TF-IDF + cosine-similarity retrieval
- Source/relevance evidence display
- PDF text extraction and document analysis
- Fully local retrieval; no Gemini, Claude, OpenAI, or API key required
- Vercel-ready Flask backend + custom HTML/CSS/JS frontend

## Local run
```bash
python -m pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.

## Vercel deployment
Push this folder to GitHub and import the repository at Vercel. Vercel detects the Flask `app` in `app.py`.

## Important
The corpus contains illustrative/demo case digests. They must be presented as synthetic/demo material, not as real judgments.

This is a research prototype and not legal advice. Verify legal material independently before relying on it.
