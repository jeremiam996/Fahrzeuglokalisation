
# Fahrzeuglokalisation (Streamlit App)

Diese App dient zur Erfassung, Lokalisierung und Statusverfolgung von Fahrzeugen auf einem Werksgelände.

## Funktionen

- Fahrzeug erfassen mit Kennzeichen & Standort
- Automatische oder manuelle Parkplatzzuweisung (A1–D5)
- Fortschrittsanzeige mit 5 Arbeitsschritten
- Visuelle Übersicht belegter & freier Parkplätze
- Lokale Speicherung in `fahrzeuge.csv`

## Deployment

1. Dieses Repository auf GitHub hochladen
2. Mit [Streamlit Cloud](https://streamlit.io/cloud) verbinden
3. Als `app.py` deployen

## Start lokal (optional)
```bash
pip install -r requirements.txt
streamlit run app.py
```
