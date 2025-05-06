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
    "Batterie ausbauen": 1,
    "Räder demontieren": 1
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

# ---- CSV vorbereiten ----
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

# ---- Admin-geschützte Funktionen: Planung + Import ----
if st.session_state.logged_in:
    st.sidebar.title("🔧 Admin-Einstellungen")
    mitarbeiter = st.sidebar.number_input("Verfügbare Mitarbeitende", min_value=1, max_value=50, value=6)

    uploaded = st.file_uploader("Excel-Datei mit Fahrzeugdaten", type=["xlsx", "csv"])
    if uploaded:
        try:
            if uploaded.name.endswith(".xlsx"):
                imp_df = pd.read_excel(uploaded)
            else:
                imp_df = pd.read_csv(uploaded)

            for step in ARBEITSSCHRITTE:
                if step not in imp_df.columns:
                    imp_df[step] = False
            if "Geplanter Tag" not in imp_df.columns:
                imp_df["Geplanter Tag"] = ""

            df = pd.concat([df, imp_df], ignore_index=True)
            st.success("Import erfolgreich.")
        except Exception as e:
            st.error("Fehler beim Import")
            st.exception(e)
else:
    mitarbeiter = 6

# ---- Automatische Tagesplanung ----
kapazitaet_pro_tag = mitarbeiter * STD_PRO_MITARBEITER
startdatum = datetime.date.today()
aktueller_tag = startdatum
tag_aufwand = 0

offene_df = df[df["Status"] != "fertig"].copy()

for idx, row in offene_df.iterrows():
    fzg_aufwand = 0
    for step, dauer in ARBEITSSCHRITTE.items():
        if step in row and not row[step]:
            fzg_aufwand += dauer

    if tag_aufwand + fzg_aufwand > kapazitaet_pro_tag:
        aktueller_tag += datetime.timedelta(days=1)
        tag_aufwand = 0

    df.at[idx, "Geplanter Tag"] = aktueller_tag
    tag_aufwand += fzg_aufwand

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

# ---- Tagesbearbeitung – heute ----
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

# ---- Status + Arbeitsschritte aktualisieren ----
def update_status_und_schritte(row):
    offene = []
    erledigt = []
    for step in ARBEITSSCHRITTE:
        if step in row:
            if row[step]:
                erledigt.append(step)
            else:
                offene.append(step)
    if len(erledigt) == len(ARBEITSSCHRITTE):
        row["Status"] = "fertig"
    elif len(erledigt) > 0:
        row["Status"] = "in Arbeit"
    else:
        row["Status"] = "angekommen"
    return pd.Series([", ".join(offene), ", ".join(erledigt), row["Status"]])

df[["Offene Schritte", "Abgeschlossene Schritte", "Status"]] = df.apply(update_status_und_schritte, axis=1)

# ---- Gesamtübersicht ----
st.subheader("📊 Gesamtübersicht mit Arbeitsfortschritt")
st.dataframe(df[[
    "Modell", "Kennzeichen", "Status", "Parkplatz", "Geplanter Tag",
    "Offene Schritte", "Abgeschlossene Schritte"
]])

df.to_csv(DATA_PATH, index=False)


