# NER Landslide Intelligence — Live Prototype

This version runs as one Django web service. The browser uses `/api/...` on the same
host, so it works on Render instead of pointing to `127.0.0.1`.

## What is real
- Live weather from Open-Meteo for nine NER monitoring locations.
- OpenStreetMap/Leaflet map.
- Explainable risk calculation using live rainfall + terrain/geological susceptibility.
- Real IoT ingestion endpoint for ESP32 devices.
- Automatic alerts when the calculated risk reaches HIGH/CRITICAL.
- No random/demo sensor stream.

## Local run
```powershell
cd backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe manage.py makemigrations monitoring
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py seed_locations
venv\Scripts\python.exe manage.py runserver
```
Open http://127.0.0.1:8000/

## Real ESP32 ingestion
POST JSON to `/api/sensors/ingest/`:
```json
{
  "sensor_id": "ESP32-01",
  "sensor_type": "SOIL",
  "location_id": 4,
  "value": 67.2,
  "unit": "%",
  "battery_level": 91
}
```
If `DEVICE_API_KEY` is configured, send it as the `X-Device-Key` header.

## Important
The risk engine is intentionally explainable rather than pretending that a trained
model exists when no validated landslide training dataset is supplied. A future
validated ML model can be plugged into `monitoring/ai_model.py`.
