import streamlit as st
from datetime import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection

col1, col2, col3 = st.columns([1,3,1])

with col2:
    st.markdown(
        "<h2 style='text-align: center;'>Hibajelentés</h2>",
        unsafe_allow_html=True
    )
    st.caption("A demo erejéig itt csak szöveg formájában")

    @st.cache_data(show_spinner = False)
    def store_user_error_data_in_excel(user_error, username):
        # Save data to Google Sheets connection defined as "gsheets_error"
        try:
            conn = st.connection("gsheets_error", type=GSheetsConnection)
            df = conn.read(ttl=0)
        except Exception as e:
            st.error(f"Nem sikerült olvasni a Google Sheet-et: {e}")
            return

        current_datetime = datetime.now()

        if df is None or isinstance(df, list):
            df = pd.DataFrame()

        if df.empty:
            df = pd.DataFrame(columns=["Hiba", "Időbélyeg", "Felhasználó"])

        cols = list(df.columns)
        new_row = {c: "" for c in cols}

        def set_value(index, value):
            if index < len(cols):
                new_row[cols[index]] = value

        if cols:
            set_value(0, user_error)
            set_value(1, current_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            set_value(2, username)
        else:
            new_row = {
                "Hiba": user_error,
                "Időbélyeg": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "Felhasználó": username,
            }
            df = pd.DataFrame(columns=new_row.keys())

        try:
            updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(data=updated)
            print("Adatok lementve Google Sheet-be.")
        except Exception as e:
            st.error(f"Nem sikerült írni a Google Sheet-be: {e}")
        




    with st.form("user_error"):

        user_error = st.text_area("Hiba leírása", height=400)


        submitted = st.form_submit_button("Küldés")
        if submitted:
            store_user_error_data_in_excel(user_error, username = st.session_state['username'])


    if submitted:
        st.success("Köszönjük a visszajelzést.")
        print(user_error)

    st.markdown(
        "<h3>Ismert hibák</h3>",
        unsafe_allow_html=True
    )
    st.write(f"""
            - A pontos találatoknál az oldalszám lehet téves.
            - A megadott válasz visszajelzésénél a "Helyes" és "Helytelen" gombok megnyomás után azok nem állnak vissza alaphelyzetbe, amíg újra rá nem kattintunk.
            - Az előző keresés "árnyéka" látható az új keresés betöltése alatt.
            - Az oldal magyarra fordítása opciót választva hibát dobhat ki a keresés.
            """)
    st.caption("Utóbbiakat egyelőre megoldja az oldal manuális újratöltése.")
