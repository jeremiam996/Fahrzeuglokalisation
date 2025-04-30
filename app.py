import streamlit as st
import pandas as pd
import os
import datetime

# ---- Konfiguration ----
DATA_PATH = "fahrzeuge.csv"
MODELLE = ["Golf", "Tiguan", "Polo", "Passat", "T-Roc"]
ARBEITSSCHRITTE = {
    "Öl ablassen": 1,
    "Batterie entfernen": 1,
    "Flüssigkeiten absaugen": 1.5,
    "Teile ausbauen": 2,
    "Dokumentation": 1
}
STD_PRO_MITARBEITER = 7

# ---- Session-Login ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    with st.form("Login"):
        st.subheader("🔑 Admin Login")
        user = st.text_input("Benutzername")
        pw = st.text_input("Passwort", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if user == "admin" and pw == "passwort123":
                st.session_state.logged_in = True
            else:
                st.error("Falsche Zugangsdaten.")

# ---- Daten laden oder anlegen ----
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=["Modell", "Kennzeichen", "Ankunftsdatum", "Status", "Parkplatz", "Geplanter Tag"] + list(ARBEITSSCHRITTE.keys()))
    df.to_csv(DATA_PATH, index=False)

# ---- Titel ----
st.title("Fahrzeuglokalisierung & Tagesplanung")

# ---- Login-Bereich ----
if not st.session_state.logged_in:
    login()
else:
    st.subheader("Neues Fahrzeug hinzufügen (nur Admin)")
    with st.form("add_vehicle"):
        modell = st.selectbox("Modell", MODELLE)
        kennz = st.text_input("Kennzeichen")
        ankunft = st.date_input("Ankunftsdatum", value=datetime.date.today())
        status = st.selectbox("Status", ["angekommen", "in Arbeit", "fertig"])
        parkplatz = st.text_input("Parkplatz (z. B. A1)")
        submitted = st.form_submit_button("Fahrzeug speichern")
        if submitted:
            new_row = {
                "Modell": modell, "Kennzeichen": kennz, "Ankunftsdatum": ankunft,
                "Status": status, "Parkplatz": parkplatz, "Geplanter Tag": ""
            }
            for step in ARBEITSSCHRITTE:
                new_row[step] = False
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DATA_PATH, index=False)
            st.success("Fahrzeug gespeichert.")

# ---- Adminfunktionen: Excelimport & Mitarbeitereingabe ----
if st.session_state.get("logged_in", False):
    st.subheader("🔐 Admin: Import & Mitarbeitereinstellungen")

    # Excelimport
    uploaded = st.file_uploader("Exceldatei hochladen", type=["xlsx", "csv"])
    if uploaded:
        try:
            ext = uploaded.name.split(".")[-1]
            if ext == "xlsx":
                imp = pd.read_excel(uploaded)
            else:
                imp = pd.read_csv(uploaded)

            for step in ARBEITSSCHRITTE:
                if step not in imp.columns:
                    imp[step] = False
            if "Geplanter Tag" not in imp.columns:
                imp["Geplanter Tag"] = ""

            df = pd.concat([df, imp], ignore_index=True)
            df.to_csv(DATA_PATH, index=False)
            st.success("Import erfolgreich.")
        except Exception as e:
            st.error("Fehler beim Import.")
            st.exception(e)

    # Mitarbeitereinstellung
    st.sidebar.title("Tagesplanung (Admin)")
    mitarbeiter = st.sidebar.number_input("Verfügbare Mitarbeitende", min_value=1, max_value=50, value=6)
else:
    mitarbeiter = 6
    st.sidebar.markdown("👷 Tagesplanung: Standardmäßig 6 Mitarbeitende (kein Admin eingeloggt)")

# ---- Tagesplanung berechnen ----
kapazitaet = mitarbeiter * STD_PRO_MITARBEITER
offen = df[df["Status"] != "fertig"].copy()
startdatum = datetime.date.today()
tag_aufwand = 0
aktueller_tag = startdatum

for idx, row in offen.iterrows():
    fzg_aufwand = 0
    for step, dauer in ARBEITSSCHRITTE.items():
        if step in row and not row[step]:
            fzg_aufwand += dauer
    if tag_aufwand + fzg_aufwand > kapazitaet:
        aktueller_tag += datetime.timedelta(days=1)
        tag_aufwand = 0
    df.at[idx, "Geplanter Tag"] = aktueller_tag
    tag_aufwand += fzg_aufwand

# ---- Tagesbearbeitung – Fahrzeuge mit geplanten Aufgaben heute ----
st.subheader("Tagesbearbeitung – heute geplante Fahrzeuge")
heute = datetime.date.today()
for idx, row in df.iterrows():
    geplant = pd.to_datetime(row["Geplanter Tag"]).date() if row["Geplanter Tag"] else None
    if geplant == heute and row["Status"] != "fertig":
        with st.expander(f"{row['Modell']} - {row['Kennzeichen']} ({row['Parkplatz']})"):
            df.at[idx, "Status"] = st.selectbox(
                "Status",
                ["angekommen", "in Arbeit", "fertig"],
                index=["angekommen", "in Arbeit", "fertig"].index(row["Status"]),
                key=f"status_{idx}"
            )
            st.markdown("**Heute geplante Schritte:**")
            offene_schritte = []
            erledigte_schritte = []
            for step in ARBEITSSCHRITTE:
                if step in row and row[step]:
                    erledigte_schritte.append(step)
                elif step in row:
                    offene_schritte.append(step)
            for step in offene_schritte:
                df.at[idx, step] = st.checkbox(f"{step}", key=f"{step}_{idx}")
            gesamt = len(ARBEITSSCHRITTE)
            erledigt = len([s for s in ARBEITSSCHRITTE if s in row and row[s]])
            st.progress(erledigt / gesamt)
            st.caption(f"{erledigt} von {gesamt} Arbeitsschritten erledigt")

# ---- Gesamtübersicht ----
st.subheader("Gesamtübersicht")
st.dataframe(df)
df.to_csv(DATA_PATH, index=False)

