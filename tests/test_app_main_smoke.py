# tests/test_app_main_smoke.py
import types
import app

class DummySpinner:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

class DummySidebar:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

def test_main_runs_happy_path(monkeypatch):
    st = app.st

    # --- stub Streamlit so nothing actually renders/stops ---
    dummy_file = types.SimpleNamespace(name="audio.mp3", size=100)
    monkeypatch.setattr(st, "file_uploader", lambda *a, **k: dummy_file)
    monkeypatch.setattr(st, "audio", lambda *a, **k: None)
    monkeypatch.setattr(st, "set_page_config", lambda *a, **k: None)
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(st, "spinner", lambda *a, **k: DummySpinner())
    monkeypatch.setattr(st, "sidebar", DummySidebar())

    # pick a tab so it renders that branch
    monkeypatch.setattr(app, "option_menu", lambda *a, **k: "Summary")

    # --- stub AWS helpers ---
    monkeypatch.setattr(app, "upload_to_s3", lambda f, n: "s3://bucket/audio.mp3")
    monkeypatch.setattr(app, "start_transcription", lambda uri: "job-123")
    monkeypatch.setattr(app, "wait_for_result", lambda job: None)
    monkeypatch.setattr(
        app, "get_transcript_from_s3",
        lambda job: ("We should deploy at 14:30 and verify the release. " * 10)
    )

    # start fresh
    st.session_state.clear()

    # should run without raising
    app.main()
