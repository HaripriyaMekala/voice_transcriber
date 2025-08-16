# tests/test_aws_utils_transcribe.py
from unittest.mock import MagicMock
import aws_utils

def test_start_transcription_calls_api(monkeypatch):
    # give aws_utils a pretend transcribe client
    fake_tr = MagicMock()
    monkeypatch.setattr(aws_utils, "_transcribe_client", lambda: fake_tr)

    s3_uri = f"s3://{aws_utils.S3_BUCKET}/uploads/fake.mp3"

    # call your real function
    job = aws_utils.start_transcription(s3_uri)

    # job name should be generated like "job-<uuid>"
    assert job.startswith("job-")

    # make sure the AWS API was called with the right stuff
    fake_tr.start_transcription_job.assert_called_once()
    _, kwargs = fake_tr.start_transcription_job.call_args

    assert kwargs["TranscriptionJobName"] == job
    assert kwargs["Media"] == {"MediaFileUri": s3_uri}
    assert kwargs["MediaFormat"] == "mp3"
    assert kwargs["LanguageCode"] == "en-US"
    assert kwargs["OutputBucketName"] == aws_utils.S3_BUCKET
