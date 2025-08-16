import streamlit as st
from collections import Counter
from textblob import TextBlob
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from streamlit_option_menu import option_menu

from aws_utils import (
    upload_to_s3,
    start_transcription,
    wait_for_result,
    get_transcript_from_s3,
)

st.set_page_config(page_title="Voice Transcriber", layout="wide")
st.markdown(
    "<h1 style='text-align:center;'>🎙️ Voice-to-Text + Meeting Notes</h1><hr>",
    unsafe_allow_html=True,
)

# ---------- helpers ----------
def summarize(text, n=5):
    if not text or len(text.split()) < 40:
        return []
    try:
        p = PlaintextParser.from_string(text, Tokenizer("english"))
        return [str(s) for s in LsaSummarizer()(p.document, n)]
    except Exception:
        return []

def action_items(text):
    blob = TextBlob(text)
    kws = [
        "we should","let’s","lets","i will","we will","you will","please","make sure","follow up",
        "schedule","assign","create","send","review","update","deploy","test","document","verify",
        "reach out","set up","setup","fix","investigate","finalize"
    ]
    items = []
    import re
    for s in blob.sentences:
        t = str(s); tl = t.lower()
        if any(k in tl for k in kws):
            m = re.search(r'(\b\d{1,2}:\d{2}(?::\d{2})?\b)', t)
            items.append({"item": t.strip(), "ts": m.group(1) if m else None})
    return items

def keywords(text, k=12):
    import re
    toks = re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())
    stop = {
        "the","and","for","that","with","this","from","have","has","are","was","were","will","would",
        "you","your","our","their","they","them","she","he","him","her","it","its","of","to","in","on",
        "at","by","as","is","be","or","an","a","we","i","but","if","so","not","do","did","done","can",
        "could","should","may","might","into","about","over","per","via","let","lets","let’s"
    }
    words = [w for w in toks if w not in stop and len(w) > 2]
    return Counter(words).most_common(k)

def file_signature(uploaded_file) -> str:
    # simple signature: name + size (Streamlit exposes .name and .size)
    # if .size not present (older versions), fall back to just name
    size = getattr(uploaded_file, "size", None)
    return f"{uploaded_file.name}:{size}" if size is not None else uploaded_file.name

# ---------- upload ----------
up = st.file_uploader("📁 Upload MP3", type=["mp3"])
if not up:
    st.info("Upload an MP3 to get started.")
    st.stop()

st.audio(up, format="audio/mp3")

# ---------- run the heavy pipeline ONCE per unique file ----------
sig = file_signature(up)

if "last_sig" not in st.session_state or st.session_state.last_sig != sig:
    # New file detected → run full pipeline and cache results
    with st.spinner("📤 Uploading to S3..."):
        s3_uri = upload_to_s3(up, up.name)

    with st.spinner("🛠️ Starting transcription..."):
        job = start_transcription(s3_uri)
        st.session_state.job = job  # show below if you like

    with st.spinner("⏳ Waiting for AWS Transcribe..."):
        wait_for_result(st.session_state.job)

    with st.spinner("📄 Fetching transcript..."):
        text = get_transcript_from_s3(st.session_state.job)

    if not text or (isinstance(text, str) and text.lower().startswith("error")):
        st.error("Failed to fetch transcript.")
        st.stop()

    # Derive once
    sumy = summarize(text, 5)
    acts = action_items(text)
    kws_ = keywords(text, 12)

    # Cache everything
    st.session_state.last_sig = sig
    st.session_state.text = text
    st.session_state.sumy = sumy
    st.session_state.acts = acts
    st.session_state.kws = kws_
    st.success("✅ Transcription complete")
else:
    # Use cached results — no S3 or Transcribe calls
    text = st.session_state.text
    sumy = st.session_state.sumy
    acts = st.session_state.acts
    kws_ = st.session_state.kws
    st.success("✅ Using cached results")

# ---------- vertical menu (sidebar) ----------
with st.sidebar:
    selected = option_menu(
        "Sections",
        ["Transcript", "Summary", "Action Items", "Keywords"],
        icons=["file-earmark-text", "chat-dots", "check2-square", "tags"],
        menu_icon="list",
        default_index=0,
        orientation="vertical",
    )

# ---------- render sections ----------
if selected == "Transcript":
    st.subheader("Transcript")
    # Optional: show job id if you want
    if "job" in st.session_state:
        st.caption(f"Job: `{st.session_state.job}`")
    st.markdown(
        f"<div style='height:420px; overflow-y:auto; border:1px solid #ccc; padding:10px; white-space:pre-wrap;'>{text}</div>",
        unsafe_allow_html=True,
    )

elif selected == "Summary":
    st.subheader("Summary")
    if sumy:
        for s in sumy:
            st.markdown(f"- {s}")
    else:
        st.info("Not enough signal to build a summary.")

elif selected == "Action Items":
    st.subheader("Action Items")
    if acts:
        for a in acts:
            ts = f"**[{a['ts']}]** " if a.get("ts") else ""
            st.markdown(f"🔹 {ts}{a['item']}")
    else:
        st.info("No clear action items detected.")

elif selected == "Keywords":
    st.subheader("Keywords")
    if kws_:
        st.write(", ".join(f"{k} ({c})" for k, c in kws_))
    else:
        st.info("No prominent keywords found.")
