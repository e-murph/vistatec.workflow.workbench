import streamlit as st
from modules.shared.styles import set_page_style, get_base64_of_bin_file

st.set_page_config(
    page_title="Vistatec Workflow Workbench",
    page_icon="assets/page_icon.png",
    layout="centered"
)

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_path="assets/banner.png"
)
# ---------------------------

# --- SIDEBAR FOOTER ---
with st.sidebar:
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")
# ----------------------

# --- HEADER WITH LOGO ---
# Convert logo to base64 so HTML can read it
logo_b64 = get_base64_of_bin_file("assets/app_icon.png")

st.markdown(
    f"""
    <style>
        /* Container ensuring perfect centering */
        .header-container {{
            display: flex;
            align-items: center; /* Vertically centers the logo and text */
            margin-bottom: 20px;
        }}
        
        /* The Logo Image */
        .header-logo {{
            width: 50px;       /* Adjust size here */
            margin-right: 20px; /* Space between logo and text */
        }}
        
        /* The Title Text */
        .header-title {{
            margin: 0;
            padding: 0;
            font-size: 3rem;   /* Matches standard Streamlit H1 size */
            font-weight: 700;
        }}
    </style>

    <div class="header-container">
        <img src="data:image/png;base64,{logo_b64}" class="header-logo">
        <h1 class="header-title">Workflow Workbench</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------

st.markdown("""
### Welcome to the Workflow Workbench utility tool hub
Select a tool from the sidebar to begin.

---

#### Available Tools:
* **📄 DOCX Track Changes Extractor:** Extract tracked changes from DOCX files.
* **📊 Phrase CSV Converter:** Convert Phrase TMS CSV analysis files into formatted Excel reports.
* **🔗 TMX Pivot Aligner:** Combine two TMX files by pivoting through a common language.
* **🌍 TMX Multilingual Splitter:** Extract specific language pairs from large multilingual TMX files.
* **🪓 TMX TU Remover:** Remove bloated translation units based on length or tag density.
* **🧹 Flare Cleaner:** Cleans MadCap Flare files and fixes errors caused by XTM filters.
* **🔐 Password Generator:** Create cryptographically secure passwords locally.

---
**Security Notice:**
* All data is processed in-memory and wiped immediately.
* Access is logged and restricted to authorized employees.
""")