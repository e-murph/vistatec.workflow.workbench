import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.tmx.cleaner import clean_tmx_files

st.set_page_config(page_title="TMX Cleaner", page_icon="🧹", layout="wide")

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
# Sidebar
with st.sidebar:
    st.header("📋 Instructions")
    st.info(
        """
        1. Set your **Character** and **Tag** thresholds.
        2. Upload TMX files.
        3. Click **Run Cleaner**.
        4. Download the cleaned TMXs + Report.
        """
    )
    st.markdown("---")
    
    if st.button("🧹 Clear Temp Files"):
        if os.path.exists("temp_tmx_clean_input"): shutil.rmtree("temp_tmx_clean_input")
        if os.path.exists("temp_tmx_clean_output"): shutil.rmtree("temp_tmx_clean_output")
        st.success("Temp folders cleared.")

    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© Vistatec 2026")

# Main Content
st.title("🧹 TMX File Cleaner")
st.markdown("""Remove bloated translation units based on length or tag density.""")
st.warning("⚠️ CONFIDENTIAL: For Internal Vistatec Use Only.")

# Settings Columns
col1, col2 = st.columns(2)
with col1:
    char_threshold = st.number_input(
        "Character Threshold (Max length per TU)", 
        min_value=100, 
        max_value=50000, 
        value=5000, 
        step=100,
        help="Any TU with more characters than this will be deleted."
    )
with col2:
    tag_threshold = st.number_input(
        "Tag Threshold (Max tags per TU)", 
        min_value=10, 
        max_value=10000, 
        value=2500, 
        step=50,
        help="Any TU with more internal tags (<ph>, <bpt>, etc.) than this will be deleted."
    )

st.markdown("---")

uploaded_files = st.file_uploader("Upload TMX Files", type=["tmx"], accept_multiple_files=True)

if st.button("Run Cleaner", type="primary") and uploaded_files:
    
    # Define Temp Folders
    INPUT_DIR = "temp_tmx_clean_input"
    OUTPUT_DIR = "temp_tmx_clean_output"
    
    # Reset Folders
    if os.path.exists(INPUT_DIR): shutil.rmtree(INPUT_DIR)
    if os.path.exists(OUTPUT_DIR): shutil.rmtree(OUTPUT_DIR)
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    status_container = st.status("Initializing...", expanded=True)
    
    try:
        # 1. Save Files
        status_container.write("📂 Saving uploaded files...")
        for up_file in uploaded_files:
            file_path = os.path.join(INPUT_DIR, up_file.name)
            with open(file_path, "wb") as f:
                f.write(up_file.getbuffer())
        
        # 2. Run Cleaning Logic
        def update_status(msg):
            status_container.write(f"⚙️ {msg}")

        files_scanned, files_cleaned, tus_removed = clean_tmx_files(
            input_folder=INPUT_DIR,
            output_folder=OUTPUT_DIR,
            char_threshold=char_threshold,
            tag_threshold=tag_threshold,
            status_callback=update_status
        )
        
        status_container.update(label="Cleaning Complete!", state="complete", expanded=False)
        
        # 3. Success Message
        st.success(f"✅ Processed {files_scanned} files. Cleaned {files_cleaned} files. Removed {tus_removed} total segments.")
        
        # 4. Zip Results
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        zip_filename = f"Cleaned_TMX_{timestamp}.zip"
        zip_path = os.path.join(OUTPUT_DIR, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(OUTPUT_DIR):
                for file in files:
                    if file != zip_filename:
                        file_path = os.path.join(root, file)
                        # Archive name should be relative to output dir so zip doesn't contain full paths
                        arcname = os.path.relpath(file_path, OUTPUT_DIR)
                        zipf.write(file_path, arcname=arcname)

        # 5. Download Button
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
