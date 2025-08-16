# tests/test_aws_utils.py
import pytest
from unittest.mock import MagicMock
import aws_utils

def test_upload_to_s3_success(monkeypatch, tmp_path):
    # make a fake S3 client
    fake_s3 = MagicMock()
    monkeypatch.setattr(aws_utils, "_s3_client", lambda: fake_s3)

    # tiny fake mp3 file
    p = tmp_path / "test.mp3"
    p.write_bytes(b"FAKEAUDIO")
    fobj = p.open("rb")

    # call your real function
    s3_uri = aws_utils.upload_to_s3(fobj, "test.mp3")

    # check: URI looks right and upload_fileobj was called with your bucket
    assert s3_uri.startswith(f"s3://{aws_utils.S3_BUCKET}/uploads/")
    fake_s3.upload_fileobj.assert_called_once()
    _, kwargs = fake_s3.upload_fileobj.call_args
    assert kwargs["Bucket"] == aws_utils.S3_BUCKET

def test_upload_to_s3_failure(monkeypatch, tmp_path):
    # important: raise a *botocore* ClientError, which your code catches
    from botocore.exceptions import ClientError
    fake_s3 = MagicMock()

    err = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Denied"}},
        operation_name="PutObject",
    )
    fake_s3.upload_fileobj.side_effect = err

    monkeypatch.setattr(aws_utils, "_s3_client", lambda: fake_s3)

    p = tmp_path / "bad.mp3"
    p.write_bytes(b"X")
    fobj = p.open("rb")

    with pytest.raises(RuntimeError) as e:
        aws_utils.upload_to_s3(fobj, "bad.mp3")
    assert "S3 upload failed" in str(e.value)
