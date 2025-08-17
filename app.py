# app.py (compact)
import re, io
import streamlit as st
from collections import Counter
from textblob import TextBlob
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from streamlit_option_menu import option_menu
from aws_utils import upload_to_s3, start_transcription, wait_for_result, get_transcript_from_s3

# ---------- helpers (kept import-safe for tests) ----------
def summarize(text, n=5):
    if not text or len(text.split()) < 40: return []
    try:
        p = PlaintextParser.from_string(text, Tokenizer("english"))
        return [str(s) for s in LsaSummarizer()(p.document, n)]
    except Exception: return []

def action_items(text):
    cues = {"we should","let’s","lets","i will","we will","you will","please","make sure","follow up","schedule","assign","create","send","review","update","deploy","test","document","verify","reach out","set up","setup","fix","investigate","finalize"}
    out=[]
    for s in TextBlob(text).sentences:
        t=str(s); tl=t.lower()
        if any(k in tl for k in cues):
            m=re.search(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", t)
            out.append({"item":t.strip(),"ts":m.group(0) if m else None})
    return out

def keywords(text, k=12):
    toks=re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())
    stop={"the","and","for","that","with","this","from","have","has","are","was","were","will","would","you","your","our","their","they","them","she","he","him","her","it","its","of","to","in","on","at","by","as","is","be","or","an","a","we","i","but","if","so","not","do","did","done","can","could","should","may","might","into","about","over","per","via","let","lets","let’s"}
    words=[w for w in toks if w not in stop and len(w)>2]
    return Counter(words).most_common(k)

def file_sig(f):
    size=getattr(f,"size",None)
    return f"{f.name}:{size}" if size is not None else f.name

# ---------- UI ----------
def main():
    st.set_page_config(page_title="Voice Transcriber", layout="wide")
    st.markdown("<h1 style='text-align:center;'>🎙️ Voice-to-Text + Meeting Notes</h1><hr>", unsafe_allow_html=True)

    up=st.file_uploader("📁 Upload MP3", type=["mp3"])
    if not up: st.info("Upload an MP3 to get started."); st.stop()
    st.audio(up, format="audio/mp3")

    sig=file_sig(up)
    if st.session_state.get("last_sig")!=sig:
        with st.spinner("📤 Uploading to S3..."): s3_uri=upload_to_s3(up, up.name)
        with st.spinner("🛠️ Starting transcription..."): st.session_state.job=start_transcription(s3_uri)
        with st.spinner("⏳ Waiting for AWS Transcribe..."): wait_for_result(st.session_state.job)
        with st.spinner("📄 Fetching transcript..."): text=get_transcript_from_s3(st.session_state.job)
        if not text or (isinstance(text,str) and text.lower().startswith("error")): st.error("Failed to fetch transcript."); st.stop()
        sumy,acts,kws_=summarize(text,5),action_items(text),keywords(text,12)
        st.session_state.update(last_sig=sig,text=text,sumy=sumy,acts=acts,kws=kws_)
        st.success("✅ Transcription complete")
    else:
        text, sumy, acts, kws_ = st.session_state.text, st.session_state.sumy, st.session_state.acts, st.session_state.kws
        st.success("✅ Using cached results")

    with st.sidebar:
        selected=option_menu("Sections", ["Transcript","Summary","Action Items","Keywords","Download"],
                             icons=["file-earmark-text","chat-dots","check2-square","tags","download"],
                             menu_icon="list", default_index=1, orientation="vertical")

    if selected=="Transcript":
        st.subheader("Transcript")
        if "job" in st.session_state: st.caption(f"Job: `{st.session_state.job}`")
        st.markdown(f"<div style='height:420px;overflow-y:auto;border:1px solid #ccc;padding:10px;white-space:pre-wrap;'>{text}</div>", unsafe_allow_html=True)

    elif selected=="Summary":
        st.subheader("Summary")
        if sumy: 
            for s in sumy: st.markdown(f"- {s}")
        else: st.info("Not enough signal to build a summary.")

    elif selected=="Action Items":
        st.subheader("Action Items")
        if acts:
            for a in acts:
                ts=f"**[{a['ts']}]** " if a.get("ts") else ""
                st.markdown(f"🔹 {ts}{a['item']}")
        else: st.info("No clear action items detected.")

    elif selected=="Keywords":
        st.subheader("Keywords")
        if kws_: st.write(", ".join(f"{k} ({c})" for k,c in kws_))
        else: st.info("No prominent keywords found.")

    elif selected=="Download":
        st.subheader("Download")
        lines=["TRANSCRIPT:", text]
        if sumy: lines+=["","SUMMARY:", *[f"- {s}" for s in sumy]]
        if acts:
            act_lines=[]
            for a in acts:
                prefix=f"[{a['ts']}] " if a.get("ts") else ""
                act_lines.append(f"- {prefix}{a['item']}")
            lines+=["","ACTION ITEMS:", *act_lines]
        if kws_: lines+=["","KEYWORDS:", ", ".join(f"{k} ({c})" for k,c in kws_)]
        payload="\n".join(lines)
        st.download_button("⬇️ Download All (.txt)", data=payload.encode("utf-8"),
                           file_name="meeting_notes.txt", mime="text/plain", use_container_width=True)

if __name__=="__main__": main()
