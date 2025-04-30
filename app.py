import streamlit as st
import pandas as pd
import os

# ---- Konfiguration ----
DATA_PATH = "fahrzeuge.csv"
ADMIN_USER = "admin"
ADMIN_PASS = "passwort123"

# ---- Session State Login ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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

# ---- CSV anlegen wenn nicht vorhanden ----
def ensure_csv():
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=["Modell", "Kennzeichen", "Ankunftsdatum", "Status", "Parkplatz"])
        df.to_csv(DATA_PATH, index=False)

# ---- Hauptlogik ----
st.title("🚗 Fahrzeugverwaltung – Adminbereich")

ensure_csv()

if not st.session_state.logged_in:
    show_login()
else:
    st.success("✅ Eingeloggt als Admin")
    st.info("Hier folgen in den nächsten Schritten: Fahrzeugerfassung, Planung, Dashboard etc.")


