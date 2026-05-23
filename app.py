import streamlit as st

ALLOWED_EMAILS = st.secrets.auth.allowed_emails

def login_screen():
    st.title("Private app")
    st.write("Please log in with Google.")
    st.button("Log in", on_click=st.login)

if not st.user.is_logged_in:
    login_screen()
    st.stop()

if st.user.email not in ALLOWED_EMAILS:
    st.error("You are not authorized to access this app.")
    st.write(f"Logged in as: {st.user.email}")
    st.button("Log out", on_click=st.logout)
    st.stop()

st.title("Hello World")
st.write(f"Welcome, {st.user.name}!")
st.button("Log out", on_click=st.logout)