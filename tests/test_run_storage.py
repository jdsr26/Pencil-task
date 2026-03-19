"""Tests for run output and standalone audit persistence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.observability import run_storage


def test_save_run_artifacts_writes_separate_audit_file(tmp_path, monkeypatch):
    outputs_dir = tmp_path / "outputs"
    audits_dir = outputs_dir / "audits"

    monkeypatch.setattr(run_storage, "OUTPUTS_DIR", outputs_dir)
    monkeypatch.setattr(run_storage, "AUDITS_DIR", audits_dir)

    result = {
        "run_id": "abc12345",
        "campaign_metadata": {"status": "complete_all_passed"},
        "final_bundle": {"ads": {"content": "x"}},
        "scores": {"ads": {"passed": True}},
        "trend_narratives": ["n1", "n2", "n3"],
        "audit_log": [{"node": "source_collect", "action": "load_and_filter"}],
    }

    paths = run_storage.save_run_artifacts(result)

    output_path = Path(paths["output_path"])
    audit_path = Path(paths["audit_path"])

    assert output_path.exists()
    assert audit_path.exists()

    audit_data = run_storage.load_audit_entries("abc12345")
    assert audit_data is not None
    assert audit_data["run_id"] == "abc12345"
    assert audit_data["total_entries"] == 1
    assert audit_data["entries"][0]["node"] == "source_collect"
