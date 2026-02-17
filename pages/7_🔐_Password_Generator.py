import streamlit as st
import pandas as pd
from modules.shared.styles import set_page_style
from modules.password.generator import generate_passwords

# 1. Page Config
st.set_page_config(page_title="Password Generator", page_icon="🔐", layout="wide")

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_path="assets/banner.png"
)

# Custom CSS
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    h1 {color: #0056b3;}
    .stButton>button {
        width: 100%;
        background-color: #0056b3;
        color: white;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# 2. Sidebar
with st.sidebar:
    st.header("📋 Instructions")
    st.info(
        """
        1. Select password **Length**.
        2. Choose **Quantity** (1-10).
        3. Toggle **Numbers/Symbols**.
        4. Click **Generate**.
        """
    )
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 3. Main Content
st.title("🔐 Secure Password Generator")
st.markdown("""Generate cryptographically strong passwords locally.""")
st.warning("⚠️ CONFIDENTIAL: Passwords are generated in-memory and never stored.")

st.markdown("---")

# --- Controls ---
col1, col2 = st.columns(2)

with col1:
    length = st.slider("Password Length", min_value=8, max_value=64, value=14)
    amount = st.slider("Quantity to Generate", min_value=1, max_value=10, value=1)

with col2:
    st.write("**Character Options**")
    use_numbers = st.checkbox("Include Numbers (0-9)", value=True)
    use_symbols = st.checkbox("Include Symbols (!@#$)", value=True)
    st.caption("*Uppercase and Lowercase letters are always included.*")

st.markdown("---")

# --- Generation Logic ---
if st.button("Generate Passwords", type="primary"):
    
    # Run the logic
    passwords = generate_passwords(amount, length, use_numbers, use_symbols)
    
    # Display Results
    st.subheader("Your Secure Passwords:")
    
    for pwd in passwords:
        # We use code blocks because they have a built-in 'copy' button on hover
        st.code(pwd, language=None)

    # Optional: CSV Download if generating many
    if amount > 1:
        df = pd.DataFrame(passwords, columns=["Generated Passwords"])
        csv = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="generated_passwords.csv",
            mime="text/csv"
        )