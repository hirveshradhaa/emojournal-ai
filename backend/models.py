from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class JournalEntry(db.Model):
    __tablename__ = "journal_entries"

    id = db.Column(db.Integer, primary_key=True)
    # Match what app.py uses: `entry=...`
    entry = db.Column(db.Text, nullable=False)

    summary = db.Column(db.Text, nullable=False)
    affirmation = db.Column(db.Text, nullable=False)

    mood = db.Column(db.String(50), nullable=False)       # e.g., "positive"
    mood_score = db.Column(db.Float, nullable=False)      # e.g., 0.56

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<JournalEntry id={self.id}>"

