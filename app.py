import streamlit as st

st.title("Secure Stock Analysis Dashboard")

# Check if the user is already authenticated
if not st.user.is_logged_in:
    st.info("Please log in to access the application dashboard.")
    
    # st.login("google") triggers the OAuth redirect loop natively
    if st.button("Log in with Google", type="primary"):
        st.login("google")
        
    st.stop()  # Stop executing the rest of the script for unauthenticated users

# --- Everything below this line runs only if the user is logged in ---

# Accessing user attributes returned by Google
user_info = st.user

st.success(f"Welcome back, {user_info.get('name', 'User')}!")

# Simple layout showcasing a protected view
col1, col2 = st.columns([1, 4])
with col1:
    if "picture" in user_info:
        st.image(user_info["picture"], width=70)
with col2:
    st.write(f"**Email:** {user_info.get('email')}")

st.markdown("---")
st.subheader("Your Secure Workspace Content")
st.write("This content is protected behind Google OAuth.")

# Log out mechanism
if st.button("Log out"):
    st.logout()