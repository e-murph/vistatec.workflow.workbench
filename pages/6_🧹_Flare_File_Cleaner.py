import streamlit as st
import os
import shutil
import zipfile
import json
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.flare.file_processing import process_files
from modules.flare.file_operations import load_language_replacements, load_replacements

st.set_page_config(page_title="Flare File Cleaner", page_icon="🧹", layout="wide")

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

# 3. Sidebar (Standardized)
with st.sidebar:
    st.header("📋 Instructions")
    st.info(
        """
        1. Select the **Target Language**.
        2. Upload your **Flare Files** (.html, .fltoc, etc).
        3. Click 'Run Cleaner'.
        4. Download the **Cleaned Files** ZIP.
        """
    )
    st.markdown("---")
    
    # Clear Temp Files Button
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_flare_input"): shutil.rmtree("temp_flare_input")
        st.success("Temp folders cleared.")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© Vistatec 2026")

# 4. Main Content
st.title("🧹 Flare File Cleaner")
st.markdown("""
Cleans MadCap Flare files and fixes errors caused by XTM filters.
* **Fixes:** Headers, List Tags, MadCap Dropdowns, XRef variations, and specific Regex patterns.
""")
st.warning("⚠️ CONFIDENTIAL: For Internal Vistatec Use Only.")

# --- 1. Load Configuration ---
try:
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

# --- 2. UI Controls ---
col1, col2 = st.columns([1, 2])

with col1:
    selected_language = st.selectbox(
        "Select Target Language",
        options=language_options,
        index=0
    )

with col2:
    uploaded_files = st.file_uploader(
        "Upload Flare Files (.html, .fltoc, .flsnp, etc.)", 
        accept_multiple_files=True
    )

# --- 3. Processing Logic ---
if st.button("Run Cleaner") and uploaded_files:
    
    TEMP_INPUT = "temp_flare_input"
    
    # Clean previous run
    if os.path.exists(TEMP_INPUT): shutil.rmtree(TEMP_INPUT)
    os.makedirs(TEMP_INPUT, exist_ok=True)
    
    status_container = st.status("Initializing...", expanded=True)
    progress_bar = status_container.progress(0)
    
    try:
        status_container.write("📂 Saving uploaded files...")
        files_saved = 0
        for uploaded_file in uploaded_files:
            file_path = os.path.join(TEMP_INPUT, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            files_saved += 1
            
        if files_saved == 0:
            st.error("No files saved.")
            st.stop()

        def update_progress(val):
            normalized = min(max(val / 100, 0.0), 1.0)
            progress_bar.progress(normalized)
            
        def update_status(msg):
            status_container.write(f"⚙️ {msg}")

        status_container.write(f"🧹 Cleaning {files_saved} files for '{selected_language}'...")
        
        process_files(
            folder_path=TEMP_INPUT,
            language=selected_language,
            progress_callback=update_progress,
            status_callback=update_status,
            language_replacements=language_replacements,
            xtm_replacements=xtm_replacements,
            madcap_replacements=madcap_replacements
        )
        
        status_container.update(label="Cleaning Complete!", state="complete", expanded=False)
        st.success("✅ Files processed successfully.")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        zip_filename = f"Cleaned_Flare_Files_{timestamp}.zip"
        zip_path = os.path.join(TEMP_INPUT, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(TEMP_INPUT):
                for file in files:
                    if file != zip_filename:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, arcname=file)

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