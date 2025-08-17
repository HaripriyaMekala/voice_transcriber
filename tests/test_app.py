import types
import app

def test_keywords_counts_and_filters():
    text = "Service deploy service test"
    result = dict(app.keywords(text, k=3))
    assert "service" in result and result["service"] >= 2
    assert "the" not in result  # stopword filtered

def test_file_sig_handles_size_and_no_size():
    f1 = types.SimpleNamespace(name="audio.mp3", size=123)
    f2 = types.SimpleNamespace(name="audio.mp3")
    assert app.file_sig(f1) == "audio.mp3:123"
    assert app.file_sig(f2) == "audio.mp3"
