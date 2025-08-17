# aws_utils.py  —  HARD-CODED CREDS (you chose Option 1)
import time, json, uuid
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

# ====== YOUR SETTINGS ======
AWS_ACCESS_KEY_ID = "REPLACE ME"
AWS_SECRET_ACCESS_KEY = "REPLACE ME"
AWS_REGION            = "us-east-1"
S3_BUCKET             = "voice-transcriber-priya-01"
# ===========================

def _s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

def _transcribe_client():
    return boto3.client(
        "transcribe",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

def _safe_key(name: str) -> str:
    # unique key to avoid collisions
    return f"uploads/{uuid.uuid4().hex}_{name.replace(' ', '_')}"

def upload_to_s3(file_obj, filename: str) -> str:
    """Uploads the audio file to S3 and returns s3:// URI."""
    key = _safe_key(filename)
    try:
        _s3_client().upload_fileobj(
            Fileobj=file_obj,
            Bucket=S3_BUCKET,
            Key=key,
            ExtraArgs={"ContentType": "audio/mpeg"}
        )
        return f"s3://{S3_BUCKET}/{key}"
    except NoCredentialsError:
        raise RuntimeError("S3 upload failed: Credentials are invalid or missing.")
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"S3 upload failed: {e}")

def start_transcription(s3_uri: str, job_name: str | None = None) -> str:
    """Starts AWS Transcribe job and returns the job name."""
    job = job_name or f"job-{uuid.uuid4()}"
    try:
        _transcribe_client().start_transcription_job(
            TranscriptionJobName=job,
            Media={"MediaFileUri": s3_uri},
            MediaFormat="mp3",
            LanguageCode="en-US",
            OutputBucketName=S3_BUCKET,  # Transcribe writes <job>.json here
        )
        return job
    except NoCredentialsError:
        raise RuntimeError("Transcribe start failed: Credentials are invalid or missing.")
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Transcribe start failed: {e}")

def wait_for_result(job_name: str, timeout_sec: int = 1800, poll: float = 3.0):
    """Polls until the job completes or fails. Raises on failure/timeout."""
    client = _transcribe_client()
    start = time.time()
    last = None
    while True:
        if time.time() - start > timeout_sec:
            raise TimeoutError("Transcription timed out.")
        try:
            r = client.get_transcription_job(TranscriptionJobName=job_name)
        except (BotoCoreError, ClientError):
            time.sleep(min(poll * 2, 10)); continue
        status = r["TranscriptionJob"]["TranscriptionJobStatus"]
        if status != last:
            print(f"{job_name} -> {status}")
            last = status
        if status == "COMPLETED":
            return r
        if status == "FAILED":
            reason = r["TranscriptionJob"].get("FailureReason", "Unknown")
            raise RuntimeError(f"Transcription failed: {reason}")
        time.sleep(poll)

def get_transcript_from_s3(job_name: str) -> str:
    """Reads <job>.json from S3 and returns the plain transcript text."""
    key = f"{job_name}.json"
    try:
        obj = _s3_client().get_object(Bucket=S3_BUCKET, Key=key)
        data = json.loads(obj["Body"].read().decode("utf-8"))
        transcripts = data.get("results", {}).get("transcripts", [])
        if not transcripts:
            raise ValueError("Transcript JSON has no 'transcripts' array.")
        return transcripts[0].get("transcript", "").strip()
    except NoCredentialsError:
        return "Error reading transcript from S3: Credentials are invalid or missing."
    except (BotoCoreError, ClientError, ValueError, json.JSONDecodeError) as e:
        return f"Error reading transcript from S3: {e}"
