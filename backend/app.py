import os
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from models import db, JournalEntry
from gpt_service import generate_summary_affirmation
from sentiment_service import analyze_sentiment

# Load .env locally; on Render, env vars are injected automatically.
load_dotenv()

app = Flask(__name__)

# --- Database config (Neon on Render, or local if you set it) ---
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Init DB
db.init_app(app)
with app.app_context():
    db.create_all()

# --- CORS (allow your deployed frontend origin if provided) ---
frontend_origin = os.getenv("FRONTEND_ORIGIN")
if frontend_origin:
    CORS(app, resources={r"/*": {"origins": [frontend_origin]}})
else:
    # Dev fallback: allow all (ok for local dev; tighten for prod)
    CORS(app)

# ---------- Routes ----------

@app.route("/health")
def health():
    """Simple health check + DB connectivity test."""
    db_ok = True
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("SELECT 1"))
    except Exception:
        db_ok = False
    return jsonify({
        "ok": True,
        "db_ok": db_ok,
        "model": os.getenv("OPENROUTER_MODEL", "openrouter/auto"),
        "time": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/journal", methods=["POST"])
def handle_journal():
    """Create one journal entry: summarize + sentiment + save (with short memory)."""
    data = request.get_json(silent=True) or {}
    entry = (data.get("entry") or "").strip()
    if not entry:
        return jsonify({"error": "Missing 'entry' text"}), 400

    # 1) Load last few entries for lightweight “memory”
    recent = (
        JournalEntry.query
        .order_by(JournalEntry.created_at.desc())
        .limit(5)
        .all()
    )
    history_texts = [j.entry for j in recent][::-1]  # oldest→newest order

    # 2) Ask LLM with counselor prompt + recent history
    summary, affirmation = generate_summary_affirmation(entry, history_texts)

    # 3) Local sentiment
    mood = analyze_sentiment(entry)  # {"mood": "...", "score": 0.x}

    # 4) Save to DB
    j = JournalEntry(
        entry=entry,
        summary=summary,
        affirmation=affirmation,
        mood=mood["mood"],
        mood_score=mood["score"],
    )
    db.session.add(j)
    db.session.commit()

    return jsonify({
        "id": j.id,
        "summary": summary,
        "affirmation": affirmation,
        "mood": mood
    }), 200


@app.route("/entries", methods=["GET"])
def list_entries():
    """List all saved entries (latest first)."""
    items = JournalEntry.query.order_by(JournalEntry.created_at.desc()).all()
    return jsonify([
        {
            "id": it.id,
            "entry": it.entry,
            "summary": it.summary,
            "affirmation": it.affirmation,
            "mood": it.mood,
            "mood_score": float(it.mood_score) if it.mood_score is not None else None,
            "created_at": it.created_at.isoformat() + "Z" if it.created_at else None,
        }
        for it in items
    ]), 200


@app.route("/entries/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id: int):
    """Delete a single entry by id."""
    it = JournalEntry.query.get(entry_id)
    if not it:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(it)
    db.session.commit()
    return jsonify({"ok": True, "deleted": entry_id}), 200


@app.route("/init-db")
def init_db():
    """Optional: safe-guarded table creation endpoint (disable in prod)."""
    if os.getenv("ALLOW_INIT_DB") != "1":
        return jsonify({"error": "init disabled"}), 403
    with app.app_context():
        db.create_all()
    return jsonify({"ok": True, "message": "Tables created"}), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True
    )
