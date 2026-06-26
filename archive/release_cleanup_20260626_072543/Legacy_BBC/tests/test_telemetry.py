# tests/test_telemetry.py
import os
import pytest
from bbc_core.telemetry import TelemetryLogger

def test_telemetry_logging(tmp_path):
    log_file = os.path.join(tmp_path, "telemetry.jsonl")
    telemetry = TelemetryLogger(log_file)
    
    telemetry.log_event("TEST_EVENT", {"info": "all_good"})
    assert telemetry.get_event_count() == 1
    
    events = telemetry.get_recent_events(limit=5)
    assert len(events) == 1
    assert events[0]["event"] == "TEST_EVENT"
    assert events[0]["data"]["info"] == "all_good"

def test_telemetry_command_metric(tmp_path):
    log_file = os.path.join(tmp_path, "telemetry.jsonl")
    telemetry = TelemetryLogger(log_file)
    
    telemetry.log_command(
        command="analyze",
        duration_sec=1.5,
        files=5,
        tokens_saved=1000,
        savings_pct=85.0
    )
    
    history = telemetry.get_command_history()
    assert len(history) == 1
    assert history[0]["data"]["command"] == "analyze"
    assert history[0]["data"]["duration_sec"] == 1.5
    
    summary = telemetry.generate_summary()
    assert summary["total_commands"] == 1
    assert summary["total_duration_sec"] == 1.5
    assert summary["total_tokens_saved"] == 1000
    assert "analyze" in summary["commands"]
