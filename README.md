1) What this app does : Upload an MP3 in your browser (Streamlit).
The app saves it to Amazon S3 and uses AWS Transcribe to produce a text transcript.
No local audio files. No LLMs. MP3 only.

2) What you need : AWS account with one S3 bucket and AWS Transcribe in the same region.
IAM (minimum): s3:PutObject, s3:GetObject, s3:ListBucket, transcribe:StartTranscriptionJob, transcribe:GetTranscriptionJob, Python 3.10+ installed.
Create a .env file: AWS_REGION=us-east-1          
AWS_S3_INPUT_BUCKET=your-input-bucket

3) Run the app : streamlit run app.py
Your browser will open automatically.

4) Use it (step-by-step) : Upload an MP3 in the Streamlit page (only .mp3 is accepted).
Click Transcribe — the app uploads to S3 and starts AWS Transcribe.
Wait while the job runs (you’ll see status in the UI).
Read the transcript on the page and Download .txt if you want a file copy (DOCX optional).

5) What you get : On-screen transcript.
.txt download (and .docx if enabled in code).
Your original MP3 stored in S3.
Transcript JSON fetched via a pre-signed URL from AWS.
Downloads: TXT (always), DOCX (if enabled).


