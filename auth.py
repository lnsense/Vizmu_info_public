import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import uuid

##col1, col2, col3 = st.columns([3,3,3])

def check_login():
    # Initialize the cookie manager
    global cookies
    col1, col2, col3 = st.columns([3,3,3])
    try:
        cookies = EncryptedCookieManager(
            prefix="TRV_Kereso",
            password="DEmo1234"
            # Replace with your own secret key
        )
    except:
        pass

    if not cookies.ready():
        st.stop()

    # Check if 'username' cookie exists
    username = cookies.get("username")

    if not username:
        # Auto-generate a stable unique ID and persist it in cookies
        generated_id = f"uid-{uuid.uuid4().hex[:12]}"
        cookies["username"] = generated_id
        cookies.save()
        return generated_id
    else:
        return username


def logout():
    if not cookies.ready():
        st.stop()

    # Clear the username cookie
    cookies["username"] = ""
    cookies.save()
    st.rerun()

if __name__ == "__main__":
    username = check_login()







