import streamlit as st

ALLOWED_EMAILS = set(st.secrets["auth"]["allowed_emails"])

if not st.user.is_logged_in:
    if st.button("Log in with Google"):
        st.login("google")
    st.stop()

if st.user.email not in ALLOWED_EMAILS:
    st.error("Not authorized")
    st.button("Log out", on_click=st.logout)
    st.stop()

st.title("Hello World")
st.write(f"Welcome {st.user.email}")