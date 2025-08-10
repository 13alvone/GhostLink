from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from ghostlink import encode_bytes_to_wav
from ghostlink.webapp.app import app


client = TestClient(app)


def test_encode_returns_wav():
    resp = client.post("/encode", data={"text": "secret"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("audio/wav")
    assert resp.content[:4] == b"RIFF"


def test_decode_known_wav():
    message = b"decode me"
    with TemporaryDirectory() as tmpdir:
        wav_path, _ = encode_bytes_to_wav(
            user_bytes=message,
            out_dir=tmpdir,
            base_name_hint="msg",
            samplerate=48000,
            baud=90.0,
            amp=0.06,
            dense=True,
            mix_profile="streaming",
            gap_ms=0.0,
            preamble_s=0.8,
            interleave_depth=4,
            repeats=2,
            ramp_ms=5.0,
            out_name=None,
        )
        with open(wav_path, "rb") as fh:
            wav_bytes = fh.read()
    files = {"wav": ("msg.wav", wav_bytes, "audio/wav")}
    resp = client.post("/decode", files=files)
    assert resp.status_code == 200
    assert resp.text.strip() == message.decode("utf-8")

