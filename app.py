import streamlit as st
import pandas as pd
import os
import datetime
import string

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
PARKPLAETZE = [f"{buchstabe}{zahl}" for buchstabe in list(string.ascii_uppercase[:5]) for zahl in range(1, 10)]

# ---- Session State ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---- Login ----
def show_login():
    with st.form("login_form"):
        st.subheader("🔑 Admin Login")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        submitted = st.form_submit_button("Login")
        if submitted and username == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.logged_in = True
            st.success("Login erfolgreich.")
        elif submitted:
            st.error("Falscher Benutzername oder Passwort")

# ---- CSV vorbereiten ----
def ensure_csv():
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=["Modell", "Kennzeichen", "Ankunftsdatum", "Status", "Parkplatz", "Geplanter Tag"] + list(ARBEITSSCHRITTE.keys()))
        df.to_csv(DATA_PATH, index=False)

# ---- App Start ----
st.title("🚗 Fahrzeugverwaltung & Dashboard")
ensure_csv()
df = pd.read_csv(DATA_PATH)
heute = datetime.date.today()

if not st.session_state.logged_in:
    show_login()
    st.stop()

# ---- Adminbereich ----
st.sidebar.title("🔧 Admin-Einstellungen")
mitarbeiter = st.sidebar.number_input("Verfügbare Mitarbeitende heute", min_value=1, max_value=50, value=6)

uploaded = st.sidebar.file_uploader("Excel-Datei importieren", type=["xlsx", "csv"])
if uploaded:
    try:
        if uploaded.name.endswith(".xlsx"):
            imp_df = pd.read_excel(uploaded)
        else:
            imp_df = pd.read_csv(uploaded)

        for step in ARBEITSSCHRITTE:
            if step not in imp_df.columns:
                imp_df[step] = False

        belegte_plaetze = set(df["Parkplatz"].dropna())
        freie_plaetze = [p for p in PARKPLAETZE if p not in belegte_plaetze]
        for i in range(len(imp_df)):
            imp_df.at[i, "Status"] = "angekommen"
            imp_df.at[i, "Geplanter Tag"] = ""
            imp_df.at[i, "Parkplatz"] = freie_plaetze[i % len(freie_plaetze)]

        df = pd.concat([df, imp_df], ignore_index=True)
        st.success("Import erfolgreich.")
    except Exception as e:
        st.error("Fehler beim Import")
        st.exception(e)

# ---- Automatische Tagesplanung ----
kapazitaet_pro_tag = mitarbeiter * STD_PRO_MITARBEITER
startdatum = heute
aktueller_tag = startdatum
tag_aufwand = 0

for idx, row in df[df["Status"] != "fertig"].iterrows():
    fzg_aufwand = sum(ARBEITSSCHRITTE[step] for step in ARBEITSSCHRITTE if step in row and not row[step])
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
    parkplatz = st.text_input("Parkplatz (leer lassen für automatisch)")
    submitted = st.form_submit_button("Fahrzeug speichern")
    if submitted:
        belegte = set(df["Parkplatz"].dropna())
        freie = [p for p in PARKPLAETZE if p not in belegte]
        platz = parkplatz if parkplatz else (freie[0] if freie else "")
        new_row = {
            "Modell": modell,
            "Kennzeichen": kennz,
            "Ankunftsdatum": heute,
            "Status": "angekommen",
            "Parkplatz": platz,
            "Geplanter Tag": ""
        }
        for step in ARBEITSSCHRITTE:
            new_row[step] = False
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.success("Fahrzeug gespeichert.")

# ---- Tagesbearbeitung ----
st.subheader("📅 Tagesbearbeitung - heute")
for idx, row in df.iterrows():
    geplant = pd.to_datetime(row["Geplanter Tag"], errors='coerce').date() if pd.notna(row["Geplanter Tag"]) else None
    if geplant == heute and row["Status"] != "fertig":
        with st.expander(f"{row['Modell']} – {row['Kennzeichen']} ({row['Parkplatz']})"):
            df.at[idx, "Status"] = st.selectbox("Status", ["angekommen", "in Arbeit", "fertig"], index=["angekommen", "in Arbeit", "fertig"].index(row["Status"]), key=f"status_{idx}")
            for step in ARBEITSSCHRITTE:
                df.at[idx, step] = st.checkbox(f"{step}", value=bool(row[step]), key=f"{step}_{idx}")

# ---- Status aktualisieren ----
def update_status(row):
    erledigt = [step for step in ARBEITSSCHRITTE if row.get(step)]
    offen = [step for step in ARBEITSSCHRITTE if not row.get(step)]
    if len(erledigt) == len(ARBEITSSCHRITTE):
        row["Status"] = "fertig"
    elif len(erledigt) > 0:
        row["Status"] = "in Arbeit"
    else:
        row["Status"] = "angekommen"
    row["Offene Schritte"] = ", ".join(offen)
    row["Abgeschlossene Schritte"] = ", ".join(erledigt)
    return row

df = df.apply(update_status, axis=1)

# ---- Dashboard ----
st.subheader("📊 Dashboard")
seiten = sorted(set(p[0] for p in PARKPLAETZE))
seite = st.selectbox("Parkplatzreihe wählen", seiten)
cols = st.columns(9)
for i, zahl in enumerate(range(1, 10)):
    platz = f"{seite}{zahl}"
    belegt = not df[df["Parkplatz"] == platz].empty
    symbol = "🚗" if belegt else "⬜"
    cols[i].markdown(f"**{platz}**<br>{symbol}", unsafe_allow_html=True)

st.markdown("### 📅 Tagesfortschritt")
heute_df = df[df["Geplanter Tag"] == str(heute)]
gesamt = len(heute_df)
fertig = sum(heute_df["Status"] == "fertig")
fortschritt = int((fertig / gesamt) * 100) if gesamt > 0 else 0
st.progress(fortschritt)
st.write(f"{fertig} von {gesamt} Fahrzeugen abgeschlossen ({fortschritt}%)")

st.markdown("### 🔮 Vorschau kommende Woche")
vorschau = df[pd.to_datetime(df["Geplanter Tag"], errors='coerce') > pd.to_datetime(heute)]
st.dataframe(vorschau[["Modell", "Kennzeichen", "Geplanter Tag", "Status"]])

# ---- Gesamtübersicht ----
st.subheader("\U0001f4cb Gesamtübersicht")
st.dataframe(df[["Modell", "Kennzeichen", "Status", "Parkplatz", "Geplanter Tag", "Offene Schritte", "Abgeschlossene Schritte"]])

# ---- Speichern ----
df.to_csv(DATA_PATH, index=False)

