import streamlit as st

st.set_page_config(page_title="Vízmű Információ Kereső",
                   page_icon=r"assets/logo_light.png",
                   layout="wide")

from datetime import datetime, timedelta
import auth
##from auth import username
import time


# Check if the user is logged in
username = auth.check_login()

if 'username' not in st.session_state:
    st.session_state['username'] = ""
st.session_state['username'] = username

# ------------------------------------------------------
# Selectable utility (TRV / DRV / ÉRV)
# ------------------------------------------------------
if 'active_utility' not in st.session_state:
    st.session_state['active_utility'] = 'TRV'

UTILITY_CONFIG = {
    'TRV': {
        'label': 'Tiszamenti Regionális Vízművek Zrt.',
        'logo': 'assets/logo_TRV.png',
        'page': 'main_page_TRV.py'
    },
    'DRV': {
        'label': 'Dunántúli Regionális Vízmű Zrt.',
        'logo': 'assets/logo_DRV.png',
        'page': 'main_page_DRV.py'
    },
    'ÉRV': {
        'label': 'Északmagyarországi Regionális Vízművek Zrt.',
        'logo': 'assets/logo_ÉRV.png',
        'page': 'main_page_ÉRV.py'
    },
}

# ---------------------- Sidebar selector ----------------------


wrap = st.sidebar.container()
with wrap:
    # st.markdown("<div class='sidebar-center-wrap'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; margin: 0 0 1px 0;'>Válassz vízművet</h3>", unsafe_allow_html=True)
    # Logos row (DRV slightly lower)
    st.markdown("<div class='sidebar-logo-row'>", unsafe_allow_html=True)
    l1, l2, l3 = st.columns([1,1,1])
    with l1:
        st.image('assets/logo_TRV.png', width=75)
    with l2:
        st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
        st.image('assets/logo_DRV.png', width=100)
    with l3:
        st.image('assets/logo_ÉRV.png', width=95)
    st.markdown("</div>", unsafe_allow_html=True)
    # Buttons row (under each logo, centered)
    # st.markdown("<div class='sidebar-btn-row'>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1,1,1])
    with b1:
        # st.markdown("<div id='btn-trv'></div>", unsafe_allow_html=True)
        if st.button("TRV", key="select_TRV_sidebar", use_container_width = 50):
            st.session_state['active_utility'] = 'TRV'
            st.rerun()
    with b2:
        # st.markdown("<div id='btn-drv'></div>", unsafe_allow_html=True)
        if st.button("DRV", key="select_DRV_sidebar", use_container_width = 50):
            st.session_state['active_utility'] = 'DRV'
            st.rerun()
    with b3:
        # st.markdown("<div id='btn-erv'></div>", unsafe_allow_html=True)
        if st.button("ÉRV", key="select_ÉRV_sidebar", use_container_width = 50):
            st.session_state['active_utility'] = 'ÉRV'
            st.rerun()
    # st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------- Front page (center logos) ----------------------
# Removed per request: only sidebar controls remain

# --------------- Sidebar config ---------------

active_key = st.session_state['active_utility']
active_page = UTILITY_CONFIG[active_key]['page']
active_title = f"{active_key} Kereső"

pages = {
    "Főoldal": [
        st.Page(active_page, title=active_title),
    ],
    "Segítség": [
        st.Page("user_manual.py", title="Használati útmutató"),
    ],
##    "Mi várható még?" [
##        st.Page("user_feedback.py", title="Rövid távon"),
##        st.Page("error_log.py", title="Hosszú távon"),
##    ],    
    "Visszajelzés": [
        st.Page("user_feedback.py", title="Felhasználói értékelés"),
        st.Page("user_error.py", title="Hibajelentés"),
    ],
}


# Use a unique key_suffix for this script
# st.sidebar.write(f"Bejelentkezve: {username}")
# if st.sidebar.button("Kijelentkezés", key="global_logout"):
#     auth.logout()
#     st.rerun()

st.sidebar.markdown(
    """
    <style>
    .creator-link {
        color: inherit !important;
    }
    .creator-link:hover {
        text-decoration: underline;
    }
    </style>

    <div style="
        font-size: 0.875rem;
        line-height: 1.5;
    ">
        Készítette:
        <a class="creator-link" href="https://epitodigital.hu" target="_blank">
            Gaál Péter
        </a>
    </div>
    """,
    unsafe_allow_html=True
)




pg = st.navigation(pages)
pg.run()
