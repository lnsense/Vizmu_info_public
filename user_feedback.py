import streamlit as st
from datetime import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection


col1, col2, col3 = st.columns([1,3,1])

with col2:
    if 'star_pressed' not in st.session_state:
        st.session_state['star_pressed'] = False
    if 'optional_user_feedback' not in st.session_state:
        st.session_state['optional_user_feedback'] = ""
    if 'user_feedback_number' not in st.session_state:
        st.session_state['user_feedback_number'] = ""

    #úgy néz ki ez nem kell
    def disable_star():
        st.session_state['star_pressed'] = True

    @st.dialog("Köszönjük az értékelést!", width="large")
    def optional_user_feedback():
        st.write("Kérlek fejtsd ki a véleményed")
        velemeny = st.text_area("")
        if st.button("Küldés"):
            st.session_state['optional_user_feedback'] = velemeny
            st.session_state['star_pressed'] = False
            st.rerun()

    def user_feedback():
        st.subheader("Kérlek értékeld a Kereső alakalmazást.")
        st.write(" ")
        
        sentiment_mapping = ["one", "two", "three", "four", "five"]
        selected = st.feedback("stars",
                               key="feedback_stars",
                               disabled=False,
                               on_change=disable_star)
        if selected is not None:
            st.success("Köszönjük!")
        if selected is not None and st.session_state['star_pressed'] == True:
            optional_user_feedback()




  
    @st.cache_data(show_spinner = False)
    def store_user_feedback_data_in_excel(user_feedback_number, user_feedback_text, username):
        # Save data to Google Sheets connection defined as "gsheets_feedback"
        try:
            conn = st.connection("gsheets_feedback", type=GSheetsConnection)
            df = conn.read(ttl=0)
        except Exception as e:
            st.error(f"Nem sikerült olvasni a Google Sheet-et: {e}")
            return

        current_datetime = datetime.now()

        if df is None or isinstance(df, list):
            df = pd.DataFrame()

        if df.empty:
            df = pd.DataFrame(columns=["Értékelés", "Vélemény", "Időbélyeg", "Felhasználó"])

        cols = list(df.columns)
        new_row = {c: "" for c in cols}

        def set_value(index, value):
            if index < len(cols):
                new_row[cols[index]] = value

        if cols:
            set_value(0, user_feedback_number)
            set_value(1, user_feedback_text)
            set_value(2, current_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            set_value(3, username)
        else:
            new_row = {
                "Értékelés": user_feedback_number,
                "Vélemény": user_feedback_text,
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

    placeholder = ""
    st.markdown(
        "<h2 style='text-align: center;'>A Kereső alkalmazásának értékelése</h2>",
        unsafe_allow_html=True
    )
    ##st.subheader("A TRV Kereső alakalmazásának értékelése.")
    st.write("")

    left, center, right = st.columns([1.3,1,1])

    with center:
        sentiment_mapping = ["1", "2", "3", "4", "5"]
        selected = st.feedback("faces",
                               key="feedback_stars",
                               disabled=False,
                               on_change=disable_star)


    if selected is not None and st.session_state['star_pressed'] == True:
        with st.form("user_error"):
    ##        optional_user_feedback()

           velemeny = st.text_area("Itt ki is fejtheted a véleményed. (Opcionális)", height=400)
           submitted = st.form_submit_button("Küldés")
           st.caption("Az értékelés csak a Küldés gomb megnyomásával véglegesíthető.")
           if submitted:
               st.session_state['optional_user_feedback'] = velemeny
               st.session_state['user_feedback_number'] = sentiment_mapping[selected]
               store_user_feedback_data_in_excel(user_feedback_number = st.session_state['user_feedback_number'],
                                                 user_feedback_text = st.session_state['optional_user_feedback'],
                                                 username = st.session_state['username'])
               st.success("KÖSZÖNJÜK!")

    










