import streamlit as st
import pandas as pd
from modules.shared.styles import set_page_style
from modules.password.generator import generate_passwords

# 1. Page Config
st.set_page_config(
    page_title="Password Generator", 
    page_icon="🔐", 
    layout="wide"
)

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_path="assets/banner.png"
)

# 2. Custom CSS (Updated for Light/Dark Mode compatibility)
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    
    /* --- DEFAULT (LIGHT MODE) STYLES --- */
    h1 {
        color: #0056b3;
    }
    .stButton>button {
        width: 100%;
        background-color: #0056b3;
        color: white;
    }
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #0056b3;
    }

    /* --- DARK MODE OVERRIDES --- */
    /* When the browser is in Dark Mode, apply these lighter colors instead */
    @media (prefers-color-scheme: dark) {
        h1 {
            color: #66b2ff; /* Lighter, highly visible blue */
        }
        .stButton>button {
            background-color: #66b2ff;
            color: #000000; /* Dark text on the light blue button for contrast */
        }
        .streamlit-expanderHeader {
            color: #66b2ff;
        }
    }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar (Clean Metadata Only)
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Placeholder for potential future settings
    st.info("No temp files are created by this tool.")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© Vistatec 2026")

# 4. Main Content Area
st.title("🔐 Secure Password Generator")

# --- NEW LAYOUT SECTION ---
# A. Description
st.markdown("""
**Generate cryptographically strong passwords locally.**
This tool creates random, complex passwords directly in your browser session. 
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Configure:** Set your desired length and character types (Numbers, Symbols).
    2. **Quantity:** Choose how many unique passwords you need.
    3. **Generate:** Click the button to create them instantly.
    4. **Copy:** Hover over the result to copy, or download the CSV if generating a batch.
    """)

st.warning("⚠️ **CONFIDENTIAL:** Passwords are generated in-memory and **never stored** or logged.")
st.markdown("---")

# 5. Controls
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Configuration")
    length = st.slider("📏 Password Length", min_value=8, max_value=64, value=14, help="Longer is stronger.")
    amount = st.slider("🔢 Quantity to Generate", min_value=1, max_value=20, value=1)

with col2:
    st.subheader("2. Character Sets")
    use_numbers = st.toggle("Include Numbers (0-9)", value=True)
    use_symbols = st.toggle("Include Symbols (!@#$)", value=True)
    st.info("ℹ️ Uppercase and Lowercase letters are always included.")

st.markdown("---")

# 6. Generation Logic
if st.button("🚀 Generate Passwords", type="primary"):
    
    # Logic is instant, no status container needed
    passwords = []
    
    try:
        passwords = generate_passwords(amount, length, use_numbers, use_symbols)
    except Exception as e:
        st.error(f"Error generating passwords: {e}")
        st.stop()

    # 7. Results Display
    st.subheader("🎉 Generated Passwords")
    
    # If single password, show it big
    if amount == 1:
        st.code(passwords[0], language=None)
        st.success("Copied to clipboard? Hover over the text above!")
        
    # If multiple, show grid
    else:
        # Display in columns for compactness
        res_col1, res_col2 = st.columns(2)
        
        for idx, pwd in enumerate(passwords):
            # Alternating columns
            target_col = res_col1 if idx % 2 == 0 else res_col2
            target_col.code(pwd, language=None)

        # CSV Download for bulk
        st.markdown("---")
        df = pd.DataFrame(passwords, columns=["Generated Passwords"])
        csv = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download List as CSV",
            data=csv,
            file_name="generated_passwords.csv",
            mime="text/csv",
            use_container_width=True
        )