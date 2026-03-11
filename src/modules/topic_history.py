"""
Topic History Tracker
=====================
JSON-based tracker that remembers past topics to prevent repeats.
Stores entries in outputs/topic_history.json with fuzzy duplicate detection.
"""

import json
import os
import re
from datetime import datetime


class TopicHistory:
    """Tracks generated topics to prevent repetition across runs."""

    MAX_HISTORY = 90  # Keep last 90 entries (~45 days at 2x/day)

    def __init__(self, filepath=None):
        if filepath is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.filepath = os.path.join(base_dir, "outputs", "topic_history.json")
        else:
            self.filepath = filepath
        self._history = self._load()

    def _load(self):
        """Load history from disk."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def _save(self):
        """Save history to disk, trimming to MAX_HISTORY."""
        self._history = self._history[-self.MAX_HISTORY:]
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self._history, f, indent=2, ensure_ascii=False)

    def add_topic(self, title, angle=None, extra=None, performance_score=0):
        """Record a generated topic with performance score.

        Args:
            title: The script/video title.
            angle: The satire angle used (e.g., 'inflation', 'education').
            extra: Optional dict of additional metadata.
            performance_score: Default zero, to be updated after upload/tracking.
        """
        entry = {
            "topic": title,
            "angle": angle or "",
            "date_used": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "performance_score": performance_score
        }
        if extra:
            entry.update(extra)
        self._history.append(entry)
        self._save()

    def get_recent_topics(self, n=20):
        """Get the last N topic titles.

        Returns:
            list[str]: Recent topic titles.
        """
        return [e.get("topic", "") for e in self._history[-n:]]

    def get_recent_entries(self, n=20):
        """Get the last N raw history entries."""
        return self._history[-n:]

    def get_recent_values(self, field, n=20):
        """Get the last N non-empty values for a field."""
        values = []
        for entry in reversed(self._history):
            value = entry.get(field)
            if value:
                values.append(value)
            if len(values) >= n:
                break
        return list(reversed(values))

    def get_recent_angles(self, n=10):
        """Get the last N satire angles used.

        Returns:
            list[str]: Recent angles.
        """
        return [e.get("angle", "") for e in self._history[-n:] if e.get("angle")]

    def is_duplicate(self, title, threshold=0.6):
        """Check if a title is too similar to recent topics.

        Uses simple word-overlap ratio for fuzzy matching.

        Args:
            title: Candidate title to check.
            threshold: Similarity ratio above which it's a duplicate.

        Returns:
            bool: True if title is likely a duplicate.
        """
        return self.is_similar_to_recent(title, field="topic", threshold=threshold, limit=30)

    def is_similar_to_recent(self, text, field="topic", threshold=0.6, limit=30):
        """Check whether text is too similar to recent values for a field."""
        candidate_words = set(self._normalize(text).split())
        if not candidate_words:
            return False

        for past in self.get_recent_values(field, limit):
            past_words = set(self._normalize(str(past)).split())
            if not past_words:
                continue
            overlap = len(candidate_words & past_words)
            union = len(candidate_words | past_words)
            if union > 0 and (overlap / union) >= threshold:
                return True
        return False

    def get_topics_used_today(self):
        """Get topics already generated today.

        Returns:
            list[str]: Titles generated today.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return [e.get("topic", "") for e in self._history if e.get("date_used") == today]

    @staticmethod
    def _normalize(text):
        """Normalize text for comparison: lowercase, remove punctuation."""
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        return re.sub(r"\s+", " ", text).strip()
