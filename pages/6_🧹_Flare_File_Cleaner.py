import streamlit as st
import os
import shutil
import zipfile
import json
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.flare.file_processing import process_files
from modules.flare.file_operations import load_language_replacements, load_replacements

# 1. Page Config
st.set_page_config(
    page_title="Flare File Cleaner", 
    page_icon="🧹", 
    layout="wide"
)

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_light_path="assets/banner_light.png",
    footer_image_dark_path="assets/banner_dark.png"
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

# 3. Sidebar (Settings Only)
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Clear Temp Files Button
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_flare_input"): shutil.rmtree("temp_flare_input")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("🧹 Flare File Cleaner")

# --- NEW LAYOUT SECTION ---
# A. Description
st.markdown("""
**Clean MadCap Flare files and fix errors caused by XTM filters.**
This tool automatically fixes common syntax issues such as broken Headers, List Tags, MadCap Dropdowns, XRef variations, and specific Regex patterns.
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Configuration:** Select the target language (this determines which cleaning rules are applied).
    2. **Upload:** Select your Flare files (`.html`, `.fltoc`, `.flsnp`, etc.).
    3. **Process:** Click **Run Cleaner**.
    4. **Download:** Get a ZIP containing the repaired files.
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# --- Load Configuration ---
try:
    # Note: Ensure these paths are correct relative to your project root
    language_replacements = load_language_replacements('settings/language_replacements.json')
    xtm_replacements = load_replacements('settings/entity_replacements.json')
    madcap_replacements = load_replacements('settings/madcapdropdown_fix.json')
    
    language_options = list(language_replacements.keys())
    
except FileNotFoundError as e:
    st.error(f"❌ Configuration Error: {e}")
    st.error("Please ensure the 'settings' folder is copied to the project root.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"❌ JSON Error: {e}")
    st.stop()

# 5. UI Controls
col1, col2 = st.columns([1, 2])

with col1:
    selected_language = st.selectbox(
        "🏳️ Select Target Language",
        options=language_options,
        index=0,
        help="Applies specific regex rules defined for this language."
    )

with col2:
    uploaded_files = st.file_uploader(
        "📂 Upload Flare Files", 
        accept_multiple_files=True,
        help="Supported formats: .html, .fltoc, .flsnp"
    )

# 6. Processing Logic
if uploaded_files:
    
    if st.button("🚀 Run Cleaner", type="primary"):
        
        TEMP_INPUT = "temp_flare_input"
        
        # Clean previous run
        if os.path.exists(TEMP_INPUT): shutil.rmtree(TEMP_INPUT)
        os.makedirs(TEMP_INPUT, exist_ok=True)
        
        # Start Status Log
        with st.status("⚙️ Initializing cleaner...", expanded=True) as status_container:
            try:
                # 1. Save Files
                status_container.write("📂 Saving uploaded files...")
                files_saved = 0
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(TEMP_INPUT, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    files_saved += 1
                
                # 2. Define Callbacks for the logic module
                # We create a progress bar inside the status container
                progress_bar = status_container.progress(0)

                def update_progress(val):
                    normalized = min(max(val / 100, 0.0), 1.0)
                    progress_bar.progress(normalized)
                    
                def update_status(msg):
                    status_container.write(f"⚙️ {msg}")

                # 3. Run Cleaning Logic
                status_container.write(f"🧹 Applying rules for '{selected_language}'...")
                
                process_files(
                    folder_path=TEMP_INPUT,
                    language=selected_language,
                    progress_callback=update_progress,
                    status_callback=update_status,
                    language_replacements=language_replacements,
                    xtm_replacements=xtm_replacements,
                    madcap_replacements=madcap_replacements
                )
                
                # 4. Zip Results
                status_container.write("📦 Packaging clean files...")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                zip_filename = f"Cleaned_Flare_Files_{timestamp}.zip"
                zip_path = os.path.join(TEMP_INPUT, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(TEMP_INPUT):
                        for file in files:
                            if file != zip_filename:
                                file_path = os.path.join(root, file)
                                zipf.write(file_path, arcname=file)

                status_container.update(label="Cleaning Complete!", state="complete", expanded=True)
                
                # 7. Results Dashboard
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                col1.metric("Files Processed", files_saved)
                col2.metric("Target Language", selected_language)

                with open(zip_path, "rb") as fp:
                    st.download_button(
                        label="📦 Download Cleaned Files (ZIP)",
                        data=fp,
                        file_name=zip_filename,
                        mime="application/zip",
                        use_container_width=True
                    )

            except Exception as e:
                status_container.update(label="Error", state="error")
                st.error(f"An error occurred: {str(e)}")