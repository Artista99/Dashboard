import streamlit as st

#st.write(st.secrets["auth"].keys())

#st.write("google" in st.secrets["auth"])

#st.stop()


ALLOWED_EMAILS = st.secrets.auth.allowed_emails

if not st.user.is_logged_in:
    st.button("Log in with Google", on_click=st.login)
    st.stop()

if st.user.email not in ALLOWED_EMAILS:
    st.error("Not authorized")
    st.button("Log out", on_click=st.logout)
    st.stop()

st.title("Hello World")
st.write(f"Welcome {st.user.email}")
