import streamlit as st
import pandas as pd
import os
import datetime

# Datenpfad
DATA_PATH = 'fahrzeuge.csv'

# Parkplatzraster A1-E9 (45 Parkplätze)
parkplaetze = [f"{chr(65 + r)}{c+1}" for r in range(5) for c in range(9)]  # 5 Reihen, 9 Spalten

# Fahrzeugdaten laden oder neu erstellen
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=["Modell", "Kennzeichen", "Ankunftsdatum", "Status", "Parkplatz", "Geplanter Tag"])
    df.to_csv(DATA_PATH, index=False)

st.title("Fahrzeuglokalisierung & Tagesplanung")

# Fahrzeug hinzufügen
st.subheader("Neues Fahrzeug erfassen")
with st.form("fahrzeug_form"):
    modell = st.text_input("Modell")
    kennzeichen = st.text_input("Kennzeichen")
    ankunftsdatum = st.date_input("Ankunftsdatum", value=datetime.date.today())
    status = st.selectbox("Status", ["angekommen", "in Arbeit", "fertig"])
    freie_plaetze = sorted(list(set(parkplaetze) - set(df["Parkplatz"].dropna())))
    parkplatz = st.selectbox("Parkplatz", freie_plaetze)
    submitted = st.form_submit_button("Fahrzeug speichern")

    if submitted:
        new_entry = pd.DataFrame([[modell, kennzeichen, ankunftsdatum, status, parkplatz, ""]],
                                 columns=["Modell", "Kennzeichen", "Ankunftsdatum", "Status", "Parkplatz", "Geplanter Tag"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)
        st.success("Fahrzeug erfolgreich gespeichert.")

# Mitarbeiteranzahl für Tagesplanung
st.sidebar.title("Tagesplanung")
mitarbeiter = st.sidebar.number_input("Mitarbeiteranzahl", min_value=1, max_value=20, value=6)
stunden_pro_mitarbeiter = 7
gesamtstunden = mitarbeiter * stunden_pro_mitarbeiter

# Annahme: 6,5h für komplette Bearbeitung eines Fahrzeugs
fahrzeuge_pro_tag = gesamtstunden / 6.5
st.sidebar.markdown(f"**Kapazität:** {fahrzeuge_pro_tag:.1f} Fahrzeuge/Tag")

# Parkplatzübersicht
st.subheader("Parkplatzbelegung")
platz_status = {platz: "frei" for platz in parkplaetze}
for _, row in df.iterrows():
    platz_status[row["Parkplatz"]] = row["Status"]

for r in range(5):
    cols = st.columns(9)
    for c in range(9):
        platz = f"{chr(65 + r)}{c+1}"
        status = platz_status.get(platz, "frei")
        farbe = "✅" if status == "fertig" else ("🛠️" if status == "in Arbeit" else ("❌" if status != "frei" else "🟩"))
        cols[c].markdown(f"**{platz}** {farbe}")

# Tagesplanung automatisch
st.subheader("Tagesplanungsvorschlag")
df_offen = df[df["Status"] != "fertig"]
df_offen = df_offen.copy()
start_datum = datetime.date.today()

for i, idx in enumerate(df_offen.index):
    geplanter_tag = start_datum + datetime.timedelta(days=i // max(1, int(fahrzeuge_pro_tag)))
    df.at[idx, "Geplanter Tag"] = geplanter_tag

st.dataframe(df)

# Änderungen speichern
df.to_csv(DATA_PATH, index=False)
