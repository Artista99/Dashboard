import streamlit as st

st.write("auth keys:", list(st.secrets["auth"].keys()))

st.write("google keys:", list(st.secrets["auth"]["google"].keys()))

st.write("client_id ends correctly:", st.secrets["auth"]["google"]["client_id"].endswith(".apps.googleusercontent.com"))

st.write("metadata url:", st.secrets["auth"]["google"]["server_metadata_url"])

st.stop()



ALLOWED_EMAILS = st.secrets.auth.allowed_emails

if not st.user.is_logged_in:
    st.button("Log in with Google", on_click=st.login("google"))
    st.stop()

if st.user.email not in ALLOWED_EMAILS:
    st.error("Not authorized")
    st.button("Log out", on_click=st.logout)
    st.stop()

st.title("Hello World")
st.write(f"Welcome {st.user.email}")
