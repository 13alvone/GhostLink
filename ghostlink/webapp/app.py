from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ghostlink.__main__ import encode_bytes_to_wav
from ghostlink.decoder import decode_wav

BASE_PATH = Path(__file__).resolve().parent


# Maximum number of bytes allowed for uploads to the encode/decode endpoints.
# This guards against excessive memory/disk usage from huge files.
MAX_UPLOAD_BYTES = 1 * 1024 * 1024  # 1 MiB
# Size of chunks to read when streaming uploads.
READ_CHUNK_BYTES = 64 * 1024

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_PATH / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/encode")
async def encode(
    text: Optional[str] = Form(None),
    file: UploadFile | None = File(None),
    samplerate: int = Form(48000),
    baud: float = Form(90.0),
    amp: float = Form(0.06),
    mode: str = Form("dense"),
    mix_profile: str = Form("streaming"),
    gap_ms: float = Form(0.0),
    preamble_s: float = Form(0.8),
    interleave_depth: int = Form(4),
    repeats: int = Form(2),
    ramp_ms: float = Form(5.0),
    out_name: Optional[str] = Form(None),
) -> Response:
    if (text not in (None, "")) and file is not None:
        raise HTTPException(status_code=400, detail="Provide either text or file, not both")
    if (text in (None, "")) and file is None:
        raise HTTPException(status_code=400, detail="Provide text or file")

    if file is not None:
        total = 0
        chunks: list[bytes] = []
        while True:
            chunk = await file.read(READ_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="File too large")
            chunks.append(chunk)
        data = b"".join(chunks)
        name_hint = file.filename or "upload"
    else:
        encoded = text.encode("utf-8")
        if len(encoded) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Text too large")
        data = encoded
        name_hint = "message"

    with TemporaryDirectory() as tmpdir:
        out_path, _ = encode_bytes_to_wav(
            user_bytes=data,
            out_dir=tmpdir,
            base_name_hint=name_hint,
            samplerate=samplerate,
            baud=baud,
            amp=amp,
            dense=(mode != "sparse"),
            mix_profile=mix_profile,
            gap_ms=gap_ms,
            preamble_s=preamble_s,
            interleave_depth=interleave_depth,
            repeats=repeats,
            ramp_ms=ramp_ms,
            out_name=(out_name or None),
        )
        with open(out_path, "rb") as fh:
            wav_bytes = fh.read()
    filename = os.path.basename(out_path)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=wav_bytes, media_type="audio/wav", headers=headers)


@app.post("/decode")
async def decode(
    wav: UploadFile = File(...),
    baud: float = Form(90.0),
    mode: str = Form("dense"),
    mix_profile: str = Form("streaming"),
    preamble_s: float = Form(0.8),
    interleave_depth: int = Form(4),
    repeats: int = Form(2),
) -> PlainTextResponse:
    with TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / (wav.filename or "input.wav")
        total = 0
        with open(wav_path, "wb") as fh:
            while True:
                chunk = await wav.read(READ_CHUNK_BYTES)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File too large")
                fh.write(chunk)
        try:
            payload = decode_wav(
                path=str(wav_path),
                baud=baud,
                dense=(mode != "sparse"),
                mix_profile=mix_profile,
                preamble_s=preamble_s,
                interleave_depth=interleave_depth,
                repeats=repeats,
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid or unsupported WAV file",
            )
    try:
        text = payload.decode("utf-8")
    except Exception:
        text = payload.decode("latin-1", errors="ignore")
    return PlainTextResponse(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="GhostLink web application")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--version", action="store_true", help="Print version and exit"
    )
    args = parser.parse_args()

    if args.version:
        import importlib.metadata

        try:
            version = importlib.metadata.version("ghostlink")
        except importlib.metadata.PackageNotFoundError:  # pragma: no cover - fallback
            version = "unknown"
        print(version)
        return

    import uvicorn

    uvicorn.run("ghostlink.webapp.app:app", host=args.host, port=args.port)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
