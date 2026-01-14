"""History manager for tracking ingestion operations.

This module provides functionality to record and retrieve the history
of bundle ingestion operations for the airgap-git-relay system.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    """Generate a unique ID for history entries."""
    return uuid.uuid4().hex[:12]


@dataclass
class HistoryEntry:
    """Record of a single ingestion operation.
    
    Attributes:
        id: Unique identifier for the entry.
        timestamp: ISO format timestamp of the ingestion.
        bundle_name: Name of the ingested bundle file.
        source_repo: Original external repository name.
        target_repo: Target internal repository name.
        profile: Profile used for the ingestion.
        status: Status of the operation ('success' or 'failed').
        error_message: Error message if status is 'failed'.
        artifacts_count: Number of artifacts included.
        duration_seconds: Duration of the operation in seconds.
    """
    id: str = field(default_factory=_generate_id)
    timestamp: str = field(default_factory=_now_iso)
    bundle_name: str = ""
    source_repo: str = ""
    target_repo: str = ""
    profile: str = "default"
    status: str = "success"  # "success" | "failed"
    error_message: str | None = None
    artifacts_count: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert history entry to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryEntry:
        """Create history entry from dictionary."""
        return cls(**data)


    def is_complete(self) -> bool:
        """Check if the entry has all required fields populated.
        
        Required fields: id, timestamp, bundle_name, source_repo, 
        target_repo, profile, status.
        
        Returns:
            True if all required fields are non-empty.
        """
        return bool(
            self.id
            and self.timestamp
            and self.bundle_name
            and self.source_repo
            and self.target_repo
            and self.profile
            and self.status
        )


class HistoryManager:
    """Manages ingestion history.
    
    Stores history entries in a JSON file with the following structure:
    {
        "entries": [
            {
                "id": "abc123",
                "timestamp": "2024-12-24T14:30:00Z",
                "bundle_name": "project-20241224T143000Z.tar.gz",
                "source_repo": "external-project",
                "target_repo": "internal/project",
                "profile": "team-alpha",
                "status": "success",
                "error_message": null,
                "artifacts_count": 3,
                "duration_seconds": 45.2
            }
        ]
    }
    """

    def __init__(self, history_file: Path | str):
        """Initialize with history file path.
        
        Args:
            history_file: Path to the history JSON file.
        """
        self.history_file = Path(history_file)
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Create history file and parent directories if they don't exist."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            self._save_data({"entries": []})

    def _load_data(self) -> dict[str, Any]:
        """Load history data from file."""
        if not self.history_file.exists():
            return {"entries": []}
        content = self.history_file.read_text(encoding="utf-8")
        return json.loads(content)

    def _save_data(self, data: dict[str, Any]) -> None:
        """Save history data to file."""
        self.history_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add_entry(self, entry: HistoryEntry) -> None:
        """Add a new history entry.
        
        Args:
            entry: HistoryEntry to add.
        """
        data = self._load_data()
        
        if "entries" not in data:
            data["entries"] = []
        
        # Add new entry at the beginning (most recent first)
        data["entries"].insert(0, entry.to_dict())
        
        self._save_data(data)

    def get_entries(self, limit: int = 50) -> list[HistoryEntry]:
        """Get history entries, most recent first.
        
        Args:
            limit: Maximum number of entries to return.
            
        Returns:
            List of HistoryEntry objects.
        """
        data = self._load_data()
        entries = data.get("entries", [])[:limit]
        return [HistoryEntry.from_dict(e) for e in entries]

    def get_entry(self, entry_id: str) -> HistoryEntry | None:
        """Get a specific history entry by ID.
        
        Args:
            entry_id: The unique ID of the entry.
            
        Returns:
            HistoryEntry if found, None otherwise.
        """
        data = self._load_data()
        for entry_data in data.get("entries", []):
            if entry_data.get("id") == entry_id:
                return HistoryEntry.from_dict(entry_data)
        return None

    def clear_history(self) -> None:
        """Clear all history entries."""
        self._save_data({"entries": []})
