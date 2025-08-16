# tests/test_aws_utils_wait_and_fetch.py
import json, types
import pytest
from unittest.mock import MagicMock
import aws_utils

def test_wait_for_result_timeout(monkeypatch):
    """
    If Transcribe keeps returning IN_PROGRESS, we should raise TimeoutError.
    We make timeout/poll very small so the test is fast.
    """
    fake_tr = MagicMock()
    fake_tr.get_transcription_job.return_value = {
        "TranscriptionJob": {"TranscriptionJobStatus": "IN_PROGRESS"}
    }
    monkeypatch.setattr(aws_utils, "_transcribe_client", lambda: fake_tr)

    with pytest.raises(TimeoutError):
        aws_utils.wait_for_result("job-xyz", timeout_sec=0.05, poll=0.01)

def test_get_transcript_from_s3_success(monkeypatch):
    """
    When S3 returns valid Transcribe JSON, we should get the transcript string.
    """
    payload = json.dumps({
        "results": {"transcripts": [{"transcript": "hello world"}]}
    }).encode("utf-8")

    fake_s3 = MagicMock()
    fake_s3.get_object.return_value = {
        "Body": types.SimpleNamespace(read=lambda: payload)
    }
    monkeypatch.setattr(aws_utils, "_s3_client", lambda: fake_s3)

    text = aws_utils.get_transcript_from_s3("job-abc")
    assert text == "hello world"
