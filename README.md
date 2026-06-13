# 🧪 Foundry Local – Chat Test

Kleines Web-Interface zum Testen eines lokal über **Foundry Local** laufenden
Modells (`qwen2.5-0.5b`). Backend: FastAPI mit Streaming, Frontend: Vanilla
HTML/JS Chat-UI.

## Voraussetzungen

- Foundry Local installiert & Dienst läuft (`foundry service status`)
- Modell gecacht: `foundry cache list` → `qwen2.5-0.5b`
- venv mit `foundry-local-sdk`, `openai`, `fastapi`, `uvicorn`

## Start

```bash
source ~/foundry-venv/bin/activate
cd ~/Repo/Tests/foundry_local
python app.py
```

Dann im Browser öffnen: **http://127.0.0.1:8765**

Der `FoundryLocalManager` startet den Dienst automatisch und lädt das Modell
beim ersten Aufruf in den Speicher (kann ein paar Sekunden dauern).

## Features

- 💬 Chat mit Verlauf (Multi-Turn)
- ⚡ Streaming-Antworten (Token für Token)
- 🌡️ Temperatur-Regler
- 🔄 Reset-Button
- ℹ️ Modell-/Endpoint-Anzeige

## Anderes Modell testen

In `app.py` die Variable `MODEL_ALIAS` ändern, z. B. auf ein anderes per
`foundry model run <alias>` getestetes Modell.
