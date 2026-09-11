"""Local, explainable legal retrieval for NyayaLens."""
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = Path(__file__).parent / "data" / "corpus.json"


class LegalRetriever:
    def __init__(self, data_path=DATA_PATH):
        with open(data_path, "r", encoding="utf-8") as f:
            self.docs = json.load(f)

        self.texts = [
            f"{d['title']}. {d['text']}"
            for d in self.docs
        ]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_df=0.95,
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(self.texts)

    def search(self, query: str, top_k: int = 6):
        if not query or not query.strip():
            return []

        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.matrix).flatten()
        ranked = scores.argsort()[::-1]

        results = []
        for idx in ranked:
            score = float(scores[idx])
            if score <= 0:
                continue
            doc = self.docs[idx]
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "source": doc["source"],
                "text": doc["text"],
                "score": round(score, 4),
                "is_demo": (
                    "Sample case digest" in doc["source"]
                    or "Illustrative" in doc["title"]
                ),
            })
            if len(results) >= top_k:
                break

        return results
