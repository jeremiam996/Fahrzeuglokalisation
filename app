import streamlit as st
import pandas as pd
import os
import datetime

# ---- Konfiguration ----
DATA_PATH = "fahrzeuge.csv"
ADMIN_USER = "admin"
ADMIN_PASS = "passwort123"

# ---- Session State Login ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---- CSV anlegen wenn nicht vorhanden ----
def ensure_csv():
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=["Modell", "Kennzeichen", "Ankunftsdatum", "Status", "Parkplatz"])
        df.to_csv(DATA_PATH, index=False)

# ---- Login-Formular ----
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

# ---- Hauptbereich Fahrzeugerfassung ----
def show_admin_interface():
    st.success("✅ Eingeloggt als Admin")

    # Bestehende Daten laden
    df = pd.read_csv(DATA_PATH)

    st.subheader("🚘 Neues Fahrzeug erfassen")
    with st.form("add_vehicle"):
        modell = st.text_input("Modell")
        kennz = st.text_input("Kennzeichen")
        ankunft = st.date_input("Ankunftsdatum", value=datetime.date.today())
        status = st.selectbox("Status", ["angekommen", "in Arbeit", "fertig"])
        parkplatz = st.text_input("Parkplatz (z. B. A1)")
        submitted = st.form_submit_button("Fahrzeug speichern")

        if submitted:
            new_row = pd.DataFrame([{
                "Modell": modell,
                "Kennzeichen": kennz,
                "Ankunftsdatum": ankunft,
                "Status": status,
                "Parkplatz": parkplatz
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_PATH, index=False)
            st.success("Fahrzeug gespeichert!")

    # Vorschau auf gespeicherte Fahrzeuge
    st.subheader("📋 Aktuelle Fahrzeugliste")
    st.dataframe(df)

# ---- Start der App ----
st.title("🚗 Fahrzeugverwaltung – Adminbereich")

ensure_csv()

if not st.session_state.logged_in:
    show_login()
else:
    show_admin_interface()
