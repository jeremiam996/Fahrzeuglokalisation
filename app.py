
import streamlit as st
import pandas as pd
import os

# Setup
DATA_PATH = "fahrzeuge.csv"
PARKPLATZ_REIHEN = ["A", "B", "C", "D"]
PARKPLATZ_SPALTEN = list(range(1, 6))
FORTSCHRITTSSTUFEN = [
    "Öl abgelassen",
    "Batterie entfernt",
    "Flüssigkeiten getrennt",
    "Komponenten demontiert",
    "Abschlusskontrolle"
]

# Daten einlesen oder initialisieren
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=["Fahrzeug", "Standort", "Fortschritt", "Status"])
    df.to_csv(DATA_PATH, index=False)

# Hilfsfunktionen
def finde_naechsten_freien_platz(belegte):
    for r in PARKPLATZ_REIHEN:
        for s in PARKPLATZ_SPALTEN:
            platz = f"{r}{s}"
            if platz not in belegte:
                return platz
    return "VOLL"

# Layout
st.set_page_config(page_title="Fahrzeuglokalisation", layout="wide")
st.title("📍 Fahrzeuglokalisation – Prototyp")

# Neueingabe
st.header("➕ Fahrzeug hinzufügen")
with st.form("add_form"):
    fahrzeug = st.text_input("Fahrzeugbezeichnung / Kennzeichen")
    belegte_plaetze = df["Standort"].tolist()
    vorgeschlagen = finde_naechsten_freien_platz(belegte_plaetze)
    manuell = st.checkbox("Standort manuell wählen")
    if manuell:
        standort = st.selectbox("Standort wählen", [f"{r}{s}" for r in PARKPLATZ_REIHEN for s in PARKPLATZ_SPALTEN if f"{r}{s}" not in belegte_plaetze])
    else:
        standort = vorgeschlagen
    fortschritt = st.selectbox("Fortschrittsstatus (optional)", [""] + FORTSCHRITTSSTUFEN)
    submitted = st.form_submit_button("🚗 Hinzufügen")
    if submitted and fahrzeug:
        df.loc[len(df)] = [fahrzeug, standort, fortschritt, "aktiv"]
        df.to_csv(DATA_PATH, index=False)
        st.success(f"{fahrzeug} wurde an Platz {standort} hinzugefügt.")

# Parkplatzübersicht
st.header("🅿️ Parkplatzbelegung")
platz_grid = {f"{r}{s}": None for r in PARKPLATZ_REIHEN for s in PARKPLATZ_SPALTEN}
status_grid = {}

for _, row in df.iterrows():
    platz_grid[row["Standort"]] = row["Fahrzeug"]
    status_grid[row["Standort"]] = row["Fortschritt"]

for r in PARKPLATZ_REIHEN:
    row_cols = st.columns(len(PARKPLATZ_SPALTEN))
    for j, s in enumerate(PARKPLATZ_SPALTEN):
        platz = f"{r}{s}"
        fahrzeug = platz_grid[platz]
        status = status_grid.get(platz, "")
        if status in ["", "None", None]:
            row_cols[j].button(f"{platz}\\n🆕 {fahrzeug}", disabled=True)
        else:
            row_cols[j].button(f"{platz}\\n🚘 {fahrzeug}", disabled=True)

        else:
            row_cols[j].button(f"{platz}\n🟩 Frei", disabled=True)

# Fortschritt bearbeiten
st.header("✏️ Fortschritt bearbeiten")
if not df.empty:
    for index, row in df.iterrows():
        col1, col2, col3 = st.columns([3, 3, 4])
        with col1:
            st.text(row["Fahrzeug"])
        with col2:
            new_status = st.selectbox(
                f"Status ändern ({row['Fahrzeug']})",
                [""] + FORTSCHRITTSSTUFEN,
                index=([""] + FORTSCHRITTSSTUFEN).index(row["Fortschritt"]) if row["Fortschritt"] in FORTSCHRITTSSTUFEN else 0,
                key=f"select_{index}"
            )
        with col3:
            if st.button("💾 Speichern", key=f"save_{index}"):
                df.at[index, "Fortschritt"] = new_status
                df.to_csv(DATA_PATH, index=False)
                st.success(f"Status von {row['Fahrzeug']} wurde aktualisiert.")
                st.experimental_rerun()

# Übersicht
st.header("📊 Übersicht aller Fahrzeuge")
st.dataframe(df)
