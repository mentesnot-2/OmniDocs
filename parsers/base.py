"""
Shared data structures and base parser interface.
"""

from dataclasses import dataclass,field
from pathlib import Path

@dataclass
class ParsedDocument:
    """Normalized output from document parsing. """

    content: str
    source_file: str
    metadata:dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.content or not self.content.strip():
            self.content = ""


def normalize_source_file(file_path: str | Path) -> str:
    """Return the canonical filename used across parsing and vector metadata."""
    return Path(file_path).name