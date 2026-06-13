"""
Foundry Local – Test-Backend
============================
Kleiner FastAPI-Server, der sich mit dem lokal laufenden Foundry-Local-Dienst
verbindet (OpenAI-kompatibler Endpoint) und ein Chat-Web-Interface bereitstellt.

Es wird bewusst das CPU-Modell verwendet:
    foundry model run qwen2.5-0.5b --device CPU
(Die GPU-Variante liefert auf Apple Silicon Kauderwelsch.)

Start:
    source ~/foundry-venv/bin/activate
    python app.py
    -> http://127.0.0.1:8765
"""

import json
import re
import subprocess
import urllib.request
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from openai import OpenAI

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
DEVICE_PREFERENCE = "cpu"      # "cpu" bevorzugen (GPU = Kauderwelsch auf Apple Silicon)
MODEL_FILTER = "qwen2.5-0.5b"  # nur Modelle mit diesem Namensbestandteil
STATIC_DIR = Path(__file__).parent / "static"


def discover_endpoint() -> str:
    """Liest die Endpoint-URL aus `foundry service status` (Port kann variieren)."""
    try:
        out = subprocess.run(
            ["foundry", "service", "status"],
            capture_output=True, text=True, timeout=15,
        ).stdout
        m = re.search(r"https?://127\.0\.0\.1:\d+", out)
        if m:
            return m.group(0).rstrip("/") + "/v1"
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  Konnte Endpoint nicht via CLI ermitteln: {exc}")
    return "http://127.0.0.1:57411/v1"  # Fallback


def pick_model(endpoint: str) -> str:
    """Holt die Modellliste vom Endpoint und wählt das passende CPU-Modell."""
    with urllib.request.urlopen(endpoint + "/models", timeout=10) as r:
        data = json.loads(r.read())["data"]
    ids = [m["id"] for m in data if MODEL_FILTER in m["id"]]
    # CPU bevorzugen
    for mid in ids:
        if DEVICE_PREFERENCE in mid.lower():
            return mid
    if not ids:
        raise RuntimeError(f"Kein Modell mit '{MODEL_FILTER}' gefunden. Verfügbar: "
                           f"{[m['id'] for m in data]}")
    return ids[0]


# ---------------------------------------------------------------------------
# Verbindung aufbauen
# ---------------------------------------------------------------------------
ENDPOINT = discover_endpoint()
MODEL_ID = pick_model(ENDPOINT)
client = OpenAI(base_url=ENDPOINT, api_key="not-needed")
print(f"✅ Verbunden. Endpoint: {ENDPOINT} | Modell: {MODEL_ID}")

app = FastAPI(title="Foundry Local Test")


class ChatRequest(BaseModel):
    messages: list[dict]
    temperature: float = 0.7


# ---------------------------------------------------------------------------
# Routen
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/info")
def info():
    return JSONResponse({
        "model_id": MODEL_ID,
        "endpoint": ENDPOINT,
        "device": DEVICE_PREFERENCE.upper(),
    })


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Streamt die Antwort des Modells als Server-Sent-Events."""

    def event_stream():
        try:
            stream = client.chat.completions.create(
                model=MODEL_ID,
                messages=req.messages,
                temperature=req.temperature,
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'token': delta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:  # noqa: BLE001 – im Test alles ans Frontend melden
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
