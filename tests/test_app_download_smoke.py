import types
import app

class DummySpinner:
    def __enter__(self): return self
    def __exit__(self, *a): return False

class DummySidebar:
    def __enter__(self): return self
    def __exit__(self, *a): return False

def test_main_download_branch(monkeypatch):
    st = app.st
    f = types.SimpleNamespace(name="a.mp3", size=1)

    # Streamlit stubs
    monkeypatch.setattr(st, "file_uploader", lambda *a, **k: f)
    for fn in ["audio","set_page_config","markdown","subheader","write",
               "caption","info","success","error","download_button"]:
        monkeypatch.setattr(st, fn, lambda *a, **k: None)
    monkeypatch.setattr(st, "spinner", lambda *a, **k: DummySpinner())
    monkeypatch.setattr(st, "sidebar", DummySidebar())

    # Choose the "Download" tab
    monkeypatch.setattr(app, "option_menu", lambda *a, **k: "Download")

    # AWS stubs
    monkeypatch.setattr(app, "upload_to_s3", lambda f, n: "s3://b/a.mp3")
    monkeypatch.setattr(app, "start_transcription", lambda uri: "job-1")
    monkeypatch.setattr(app, "wait_for_result", lambda job: None)
    monkeypatch.setattr(
        app, "get_transcript_from_s3",
        lambda job: ("We should deploy at 14:30 and verify the release thoroughly across services. " * 40)
    )

    # fresh session
    st.session_state.clear()

    # run: should build payload and call st.download_button
    app.main()
