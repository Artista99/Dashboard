import streamlit as st

st.title("Ignacio's Dashboard")

# 1. Trigger the native Google login loop
if not st.user.is_logged_in:
    st.info("Please log in to access the application dashboard.")
    if st.button("Log in with Google", type="primary"):
        st.login("google")
    st.stop()

# 2. Get user info and allowed emails from secrets
user_info = st.user
user_email = user_info.get("email", "").lower()
allowed_list = [email.lower() for email in st.secrets["app_access"]["allowed_emails"]]

# 3. Enforce access control restriction
if user_email not in allowed_list:
    st.error(f"Access Denied: The account {user_email} is not authorized to view this application.")
    if st.button("Log out / Switch Account"):
        st.logout()
    st.stop()

# --- Everything below this line is fully secure and restricted ---
st.success(f"Access Granted. Welcome back, {user_info.get('name')}!")
st.write("Your secure data and Streamlit metrics go here.")