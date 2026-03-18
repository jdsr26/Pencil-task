"""
Source Registry
===============
Indexes source records for fast lookup during claim-linking
and evidence checking.
"""

import json
from typing import List, Optional

from backend.pipeline.state import SourceRecord


class SourceRegistry:
    """Indexes source records for lookup by ID, tag, or keyword."""

    def __init__(self):
        self.records: List[SourceRecord] = []
        self._by_id = {}

    def load_from_file(self, filepath: str):
        """Load and validate source records from JSON file."""
        with open(filepath, "r") as f:
            raw_records = json.load(f)
        for raw in raw_records:
            record = SourceRecord(**raw)  # Pydantic validates each record
            self.records.append(record)
            self._by_id[record.id] = record

    def add_record(self, record: SourceRecord):
        """Add a single record (used for synthetic supplements)."""
        self.records.append(record)
        self._by_id[record.id] = record

    def get_by_id(self, record_id: str) -> Optional[SourceRecord]:
        """Lookup by ID."""
        return self._by_id.get(record_id)

    def get_by_category(self, category: str) -> List[SourceRecord]:
        """Get all records in a category."""
        return [r for r in self.records if r.category == category]

    def get_by_tag(self, tag: str) -> List[SourceRecord]:
        """Get all records with a specific trend tag."""
        return [r for r in self.records if tag in r.trend_tags]

    def get_all_claims(self) -> List[dict]:
        """Get all claims from all records — used by claim_linker."""
        claims = []
        for record in self.records:
            for claim in record.key_claims:
                claims.append({"claim": claim, "source_id": record.id, "source_name": record.source_name})
        return claims

    def get_categories_covered(self) -> set:
        """Get unique categories — used by evidence_check."""
        return {r.category for r in self.records}

    def get_all_records(self) -> List[SourceRecord]:
        """Return all records."""
        return self.records