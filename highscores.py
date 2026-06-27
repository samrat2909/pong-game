"""
PONG STRIKE - High Score Manager
Persistent high score tracking using JSON file storage.
"""

import json
import os
from datetime import datetime

from constants import HIGH_SCORES_FILE, MAX_HIGH_SCORES


class HighScoreManager:
    """Manages reading, writing, and displaying high scores."""

    def __init__(self, filepath=HIGH_SCORES_FILE):
        self.filepath = filepath
        self.scores = self._load()

    def _load(self):
        """Load high scores from the JSON file."""
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
                # Validate structure
                if isinstance(data, list):
                    return [
                        entry for entry in data
                        if isinstance(entry, dict) and "score" in entry and "date" in entry
                    ][:MAX_HIGH_SCORES]
        except (json.JSONDecodeError, IOError):
            pass
        return []

    def _save(self):
        """Save high scores to the JSON file."""
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.scores[:MAX_HIGH_SCORES], f, indent=2)
        except IOError:
            pass  # Silently fail - scores won't persist but game continues

    def add_score(self, score, difficulty="Medium"):
        """Add a score if it qualifies for the high score list."""
        entry = {
            "score": score,
            "difficulty": difficulty,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.scores.append(entry)
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:MAX_HIGH_SCORES]
        self._save()
        return self.is_high_score(score)

    def is_high_score(self, score):
        """Check if a score would make the high score list."""
        if len(self.scores) < MAX_HIGH_SCORES:
            return True
        if self.scores and score > self.scores[-1]["score"]:
            return True
        if not self.scores:
            return True
        return False

    def get_scores(self):
        """Get the current high score list."""
        return list(self.scores)

    def get_top_score(self):
        """Get the highest score."""
        if self.scores:
            return self.scores[0]["score"]
        return 0

    def clear(self):
        """Clear all high scores."""
        self.scores = []
        self._save()
