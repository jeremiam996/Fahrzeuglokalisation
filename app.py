
import streamlit as st
import pandas as pd
import os

# Datenpfad
DATA_PATH = 'fahrzeuge.csv'

# Parkplatzraster
parkplaetze = [f"{chr(65 + r)}{c+1}" for r in range(4) for c in range(4)]  # A1-D4

# Initialdaten laden oder erstellen
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=["Modell", "Kennzeichen", "Status", "Parkplatz"])
    df.to_csv(DATA_PATH, index=False)

# App-Layout
st.title("Fahrzeuglokalisierung – Recycling Standort")

# Fahrzeug hinzufügen
st.subheader("Neues Fahrzeug erfassen")
with st.form("fahrzeug_form"):
    modell = st.text_input("Modell")
    kennzeichen = st.text_input("Kennzeichen")
    status = st.selectbox("Status", ["angekommen", "in Arbeit", "fertig"])
    freier_platz = list(set(parkplaetze) - set(df["Parkplatz"].dropna()))
    parkplatz = st.selectbox("Parkplatz", sorted(freier_platz))
    submitted = st.form_submit_button("Fahrzeug speichern")

    if submitted:
        new_entry = pd.DataFrame([[modell, kennzeichen, status, parkplatz]],
                                 columns=["Modell", "Kennzeichen", "Status", "Parkplatz"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)
        st.success("Fahrzeug erfolgreich hinzugefügt!")

# Parkplatzübersicht
st.subheader("Parkplatzbelegung")

platz_status = {platz: "frei" for platz in parkplaetze}
for _, row in df.iterrows():
    platz_status[row["Parkplatz"]] = row["Status"]

for r in range(4):
    cols = st.columns(4)
    for c in range(4):
        platz = f"{chr(65 + r)}{c+1}"
        farbe = "✅" if platz_status[platz] == "fertig" else ("🛠️" if platz_status[platz] == "in Arbeit" else ("❌" if platz_status[platz] != "frei" else "🟩"))
        cols[c].markdown(f"**{platz}**: {farbe}")

# Fahrzeugliste
st.subheader("Alle Fahrzeuge")
st.dataframe(df)
