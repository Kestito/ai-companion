"""
Memory types module for the AI Companion.

This module defines common types used across the memory system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass
class Memory:
    """Memory object representing a single memory entry."""

    id: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    patient_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary format."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "patient_id": self.patient_id,
        }


# Type alias for a list of memories
Memories = List[Memory]
