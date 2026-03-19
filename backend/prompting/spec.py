"""Canonical, model-agnostic prompt specification."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PromptSpec:
    """Canonical prompt intent independent of model formatting."""

    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    feedback: Optional[List[str]] = None
