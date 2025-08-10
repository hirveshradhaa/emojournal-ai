import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from gpt_service import generate_summary_affirmation
from sentiment_service import analyze_sentiment
from models import db, JournalEntry

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

@app.route("/journal", methods=["POST"])
def handle_journal():
    data = request.get_json()
    entry = data.get("entry", "")

    # Guard against empty input
    if not entry.strip():
        return jsonify({"error": "entry is required"}), 400

    summary, affirmation = generate_summary_affirmation(entry)
    mood = analyze_sentiment(entry)

    journal = JournalEntry(
        entry=entry,            # field name must match your model
        summary=summary,
        affirmation=affirmation,
        mood=mood["mood"],
        mood_score=mood["score"]
    )

    db.session.add(journal)
    db.session.commit()

    return jsonify({
        "summary": summary,
        "affirmation": affirmation,
        "mood": mood
    }), 200
from sqlalchemy import desc

@app.route("/entries", methods=["GET"])
def list_entries():
    entries = JournalEntry.query.order_by(desc(JournalEntry.id)).limit(50).all()
    data = [
        {
            "id": e.id,
            "entry": e.entry,
            "summary": e.summary,
            "affirmation": e.affirmation,
            "mood": e.mood,
            "mood_score": e.mood_score,
        }
        for e in entries
    ]
    return jsonify(data), 200
@app.route("/health")
def health():
    return {"ok": True}, 200

@app.route("/entries/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    e = JournalEntry.query.get(entry_id)
    if not e:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(e)
    db.session.commit()
    return jsonify({"ok": True}), 200
@app.route("/stats", methods=["GET"])
def stats():
    total = db.session.query(func.count(JournalEntry.id)).scalar() or 0
    avg_score = db.session.query(func.avg(JournalEntry.mood_score)).scalar()
    avg_score = round(float(avg_score), 4) if avg_score is not None else None

    by_mood = (
        db.session.query(JournalEntry.mood, func.count(JournalEntry.id))
        .group_by(JournalEntry.mood)
        .all()
    )
    mood_counts = {m: c for m, c in by_mood}

    return jsonify({
        "total_entries": total,
        "avg_mood_score": avg_score,
        "mood_counts": mood_counts
    }), 200
if __name__ == "__main__":
    app.run(debug=True)
