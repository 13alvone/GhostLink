from fastapi.testclient import TestClient

from ghostlink.webapp.app import app


client = TestClient(app)


def test_encode_decode_cycle():
    resp = client.post("/encode", data={"text": "secret"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("audio/wav")

    wav_bytes = resp.content
    files = {"wav": ("msg.wav", wav_bytes, "audio/wav")}
    resp2 = client.post("/decode", files=files)
    assert resp2.status_code == 200
    assert resp2.text.strip() == "secret"


def test_get_index_page():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "GhostLink Web Interface" in resp.text
