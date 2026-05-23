import streamlit as st
import os

st.title("🛡️ Streamlit OAuth Diagnostic Panel")
st.write("This page checks your cloud configuration live to find why the authentication loop is breaking.")

# --- TEST 1: Check Secrets Parsing ---
st.header("1. Configuration & Secrets Check")
try:
    auth_secrets = st.secrets.get("auth", {})
    google_secrets = st.secrets.get("auth", {}).get("google", {})
    app_access = st.secrets.get("app_access", {})
    
    st.success("✅ Streamlit successfully parsed the secrets TOML structure.")
    
    # Check individual keys without showing sensitive values completely
    st.write(f"**Has Cookie Secret:** {'✅ Yes' if 'cookie_secret' in auth_secrets else '❌ Missing'}")
    st.write(f"**Has Google Client ID:** {'✅ Yes' if 'client_id' in google_secrets else '❌ Missing'}")
    st.write(f"**Has Google Client Secret:** {'✅ Yes' if 'client_secret' in google_secrets else '❌ Missing'}")
    st.write(f"**Has App Access Block:** {'✅ Yes' if app_access else '❌ Missing'}")
    
except Exception as e:
    st.error(f"❌ Failed to parse secrets: {e}")

---

# --- TEST 2: URL & Environment Consistency Check ---
st.header("2. URL Match Validation")

# Detect the current URL from Streamlit's internal header system
ctx_headers = st.context.headers
host_header = ctx_headers.get("Host", "Not Found")
st.write(f"**Live Browser Host Detected:** `https://{host_header}`")

# Get what you configured in the secrets dashboard
configured_uri = auth_secrets.get("redirect_uri", "NOT CONFIGURED")
st.write(f"**Your Configured Redirect URI:** `{configured_uri}`")

# Run the alignment math
expected_uri = f"https://{host_header}/oauth2callback"
if configured_uri.strip() == expected_uri.strip():
    st.success("✅ Perfect Alignment! Your configuration matches your live browser URL.")
else:
    st.error(f"❌ MISMATCH DETECTED!")
    st.code(f"Your secret says: {configured_uri}\nBut the live app expects: {expected_uri}")
    st.info("If these do not match character-for-character, Google will drop the connection instantly.")

---

# --- TEST 3: Check Environment & Libraries ---
st.header("3. Package Dependency Verification")
try:
    import authlib
    st.success(f"✅ `authlib` is installed correctly (Version: {authlib.__version__})")
except ImportError:
    st.error("❌ `authlib` is missing entirely from the production container. Check your requirements.txt.")

---

# --- TEST 4: The Live Trigger ---
st.header("4. Test OAuth Handshake Trigger")
st.write("If the checks above are green, click below to try triggering the native framework. Watch closely to see if it immediately goes white or drops an internal error.")

if not st.user.is_logged_in:
    if st.button("Test Login Loop", type="primary"):
        try:
            st.login("google")
        except Exception as err:
            st.exception(err)
else:
    st.success(f"Successfully Authenticated as: {st.user.get('email')}")
    if st.button("Log out"):
        st.logout()