"""
Shared data structures and base parser interface.
"""

from dataclasses import dataclass,field
from typing import Optional

@dataclass
class ParsedDocument:
    """Normalized output from document parsing. """

    content: str
    source_file: str
    metadata:dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.content or not self.content.strip():
            self.content = ""