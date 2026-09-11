"""NyayaLens - Commercial Court Intelligence Engine.

Vercel-ready Flask application. Fully local retrieval PoC/MVP:
no Gemini, Claude, OpenAI, or API key required.
"""
import re
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from retrieval import LegalRetriever

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

BASE_DIR = Path(__file__).resolve().parent

# Vercel serves files in /public through Flask's static route.
app = Flask(
    __name__,
    static_folder="public",
    static_url_path="/static",
    template_folder="templates",
)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

retriever = LegalRetriever()


def build_local_answer(query, results):
    if not results:
        return {
            "heading": "No sufficiently relevant material found",
            "summary": "Try rephrasing the query or expand the knowledge base.",
            "points": [],
        }

    q = query.lower()
    joined = " ".join(r["text"] for r in results).lower()
    points = []

    if "12a" in q or "mediation" in q or "pre-institution" in q:
        if "12a" in joined or "pre-institution" in joined:
            points.append(
                "For a commercial suit that does not contemplate urgent interim relief, "
                "the knowledge base states that pre-institution mediation under Section 12A "
                "must be exhausted before institution."
            )

    if "written statement" in q or "120 days" in q or "delay" in q:
        if "120 days" in joined:
            points.append(
                "The retrieved material states that commercial suits have a 120-day outer "
                "limit for filing the written statement under the amended CPC framework."
            )

    if "specified value" in q or "3 lakh" in q or "threshold" in q:
        if "specified value" in joined:
            points.append(
                "The corpus identifies ₹3 lakh as the baseline Specified Value threshold, "
                "subject to any higher notified value."
            )

    if "commercial dispute" in q or "jurisdiction" in q or "commercial court" in q:
        if "commercial dispute" in joined:
            points.append(
                "Section 2 material in the knowledge base covers a broad range of commercial "
                "transactions and agreements within the statutory definition of commercial dispute."
            )

    if not points:
        top = results[0]
        points.append(
            f"The strongest retrieved authority is {top['title']} "
            f"(reference {top['id']}) with a relevance score of {top['score']:.2f}."
        )
        if len(results) > 1:
            points.append(
                f"Additional supporting material was retrieved from {len(results) - 1} other sources."
            )

    return {
        "heading": "Research finding",
        "summary": "This answer is generated from the local knowledge base only; it is not an external legal opinion.",
        "points": points,
    }


def extract_pdf_text(file_bytes):
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed.")
    reader = PdfReader(BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def extract_section(text, labels, max_chars=900):
    lower = text.lower()
    positions = []
    for label in labels:
        pos = lower.find(label.lower())
        if pos >= 0:
            positions.append(pos)
    if not positions:
        return ""
    chunk = text[min(positions):min(positions) + max_chars]
    return re.sub(r"\s+", " ", chunk).strip()


def summarize_document(text):
    clean = re.sub(r"\s+", " ", text).strip()
    parties = extract_section(clean, ["Parties", "Plaintiff", "Petitioner", "Appellant"], 650)
    facts = extract_section(clean, ["Key Facts", "Facts", "Background", "Case Facts"], 900)
    issues = extract_section(clean, ["Legal Issue", "Issues", "Question for Research", "Issues Raised"], 800)

    if not parties:
        m = re.search(r"(.{0,120}(?:vs\.?|versus|v\.) .{0,180})", clean, re.I)
        parties = m.group(1).strip() if m else "Parties were not explicitly identified in the extracted text."
    if not facts:
        facts = clean[:900] if clean else "No extractable facts were found."
    if not issues:
        issues = "No explicit legal-issue heading was detected. Review the retrieved legal sources for the closest statutory provisions."

    return {"parties": parties, "facts": facts, "issues": issues, "characters": len(clean)}


@app.get("/")
def index():
    return render_template("index.html", corpus_size=len(retriever.docs))


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "corpus_size": len(retriever.docs),
        "mode": "local-retrieval",
    })


@app.post("/api/search")
def search():
    try:
        payload = request.get_json(silent=True) or {}
        query = str(payload.get("query", "")).strip()
        if not query:
            return jsonify({"error": "Please enter a legal research question."}), 400

        results = retriever.search(query, top_k=6)
        return jsonify({
            "query": query,
            "answer": build_local_answer(query, results),
            "results": results,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/summarize")
def summarize():
    try:
        file = request.files.get("file")
        if not file or not file.filename:
            return jsonify({"error": "Please choose a PDF file."}), 400
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported."}), 400

        pdf_bytes = file.read()
        text = extract_pdf_text(pdf_bytes)
        if not text:
            return jsonify({"error": "No text could be extracted. The PDF may be scanned/image-based."}), 400

        results = retriever.search(text[:1800], top_k=6)
        return jsonify({
            "filename": file.filename,
            "summary": summarize_document(text),
            "results": results,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
