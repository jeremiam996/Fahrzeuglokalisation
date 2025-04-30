import streamlit as st
import pandas as pd
import os
import datetime

# ---- Konfiguration ----
DATA_PATH = "fahrzeuge.csv"
ADMIN_USER = "admin"
ADMIN_PASS = "passwort123"
ARBEITSSCHRITTE = {
    "Öl ablassen": 1,
    "Batterie entfernen": 1,
    "Flüssigkeiten absaugen": 1.5,
    "Teile ausbauen": 2,
    "Dokumentation": 1
}
MODELLE = ["Golf", "Tiguan", "Polo", "Passat", "T-Roc"]
STD_PRO_MITARBEITER = 7

# ---- Session State ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---- Login-Funktion ----
def show_login():
    with st.form("login_form"):
        st.subheader("🔑 Admin Login")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state.logged_in = True
                st.success("Login erfolgreich.")
            else:
                st.error("Falscher Benutzername oder Passwort.")

# ---- CSV-Datei vorbereiten ----
def ensure_csv():
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=["Modell", "Kennzeichen", "Ankunftsdatum", "Status", "Parkplatz", "Geplanter Tag"] + list(ARBEITSSCHRITTE.keys()))
        df.to_csv(DATA_PATH, index=False)

# ---- App Start ----
st.title("🚗 Fahrzeugverwaltung & Tagesbearbeitung")
ensure_csv()
df = pd.read_csv(DATA_PATH)

# ---- Login anzeigen ----
if not st.session_state.logged_in:
    show_login()
    st.stop()

# ---- Neues Fahrzeug erfassen ----
st.subheader("🚘 Neues Fahrzeug erfassen")
with st.form("add_vehicle"):
    modell = st.selectbox("Modell", MODELLE)
    kennz = st.text_input("Kennzeichen")
    ankunft = st.date_input("Ankunftsdatum", value=datetime.date.today())
    status = st.selectbox("Status", ["angekommen", "in Arbeit", "fertig"])
    parkplatz = st.text_input("Parkplatz (z. B. A1)")
    submitted = st.form_submit_button("Fahrzeug speichern")
    if submitted:
        new_row = {
            "Modell": modell,
            "Kennzeichen": kennz,
            "Ankunftsdatum": ankunft,
            "Status": status,
            "Parkplatz": parkplatz,
            "Geplanter Tag": ""
        }
        for step in ARBEITSSCHRITTE:
            new_row[step] = False
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)
        st.success("Fahrzeug gespeichert!")

# ---- Tagesbearbeitung: Heute geplante Fahrzeuge ----
st.subheader("📅 Tagesbearbeitung – heute")
heute = datetime.date.today()

for idx, row in df.iterrows():
    geplant = pd.to_datetime(row["Geplanter Tag"]).date() if pd.notna(row["Geplanter Tag"]) and row["Geplanter Tag"] != "" else None
    if geplant == heute and row["Status"] != "fertig":
        with st.expander(f"{row['Modell']} – {row['Kennzeichen']} ({row['Parkplatz']})"):
            df.at[idx, "Status"] = st.selectbox(
                "Status",
                ["angekommen", "in Arbeit", "fertig"],
                index=["angekommen", "in Arbeit", "fertig"].index(row["Status"]),
                key=f"status_{idx}"
            )
            st.markdown("**Heute geplante Arbeitsschritte:**")
            for step in ARBEITSSCHRITTE:
                if step in row:
                    df.at[idx, step] = st.checkbox(f"{step}", value=bool(row[step]), key=f"{step}_{idx}")

# ---- Arbeitsfortschritt berechnen ----
def get_schritte_status(row):
    offene = []
    erledigt = []
    for step in ARBEITSSCHRITTE:
        if step in row:
            if row[step]:
                erledigt.append(step)
            else:
                offene.append(step)
    return ", ".join(offene), ", ".join(erledigt)

# ---- Gesamtübersicht mit Fortschritt ----
st.subheader("📊 Gesamtübersicht mit Arbeitsfortschritt")
df["Offene Schritte"], df["Abgeschlossene Schritte"] = zip(*df.apply(get_schritte_status, axis=1))

st.dataframe(df[[
    "Modell", "Kennzeichen", "Status", "Parkplatz", "Geplanter Tag",
    "Offene Schritte", "Abgeschlossene Schritte"
]])

# ---- Speichern ----
df.to_csv(DATA_PATH, index=False)

