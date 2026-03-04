import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.tmx.cleaner import clean_tmx_files

# 1. Page Config
st.set_page_config(
    page_title="TMX TU Remover", 
    page_icon="🪓", 
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
        if os.path.exists("temp_tmx_clean_input"): shutil.rmtree("temp_tmx_clean_input")
        if os.path.exists("temp_tmx_clean_output"): shutil.rmtree("temp_tmx_clean_output")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("🪓 TMX TU Remover")

# --- NEW LAYOUT SECTION ---
# A. Description
st.markdown("""
**Remove bloated translation units based on length or tag density.** This tool scans TMX files and removes segments that exceed specific character or tag limits.
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Configure Thresholds:** Set the maximum allowed characters and tags per segment.
    2. **Upload Files:** Select one or multiple TMX files.
    3. **Process:** Click **Run Cleaner**.
    4. **Download:** Save a ZIP containing the cleaned TMX files and a detailed report.
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. Configuration Columns
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

# 6. File Uploader & AI Toggle
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_files = st.file_uploader(
        "📂 Upload TMX Files", 
        type=["tmx"], 
        accept_multiple_files=True
    )
with col_up2:
    st.write("<br>", unsafe_allow_html=True) # Spacer for alignment
    enable_ai = st.toggle("✨ Enable AI Semantic QE", help="Uses Gemini to identify severe mistranslations.")
    
    # --- DYNAMIC AI WARNING ---
    if enable_ai:
        st.markdown("""
        <div style="font-size: 0.8em; color: #666; margin-top: 10px; line-height: 1.2;">
            🤖 <b>Note:</b> Gemini is AI and can make mistakes. Please review all AI outputs manually.<br>
            <a href="https://support.google.com/gemini/answer/13594961" target="_blank">Your privacy & Gemini</a>
        </div>
        """, unsafe_allow_html=True)

if uploaded_files:
    if st.button("🚀 Run Cleaner", type="primary"):
        
        # Define Temp Folders
        INPUT_DIR = "temp_tmx_clean_input"
        OUTPUT_DIR = "temp_tmx_clean_output"
        
        # Reset Folders
        if os.path.exists(INPUT_DIR): shutil.rmtree(INPUT_DIR)
        if os.path.exists(OUTPUT_DIR): shutil.rmtree(OUTPUT_DIR)
        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Start Status Log
        with st.status("⚙️ Cleaning TMX files...", expanded=True) as status_container:
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

                # --- AI FLAG ADDED TO THIS FUNCTION CALL ---
                files_scanned, files_cleaned, tus_removed = clean_tmx_files(
                    input_folder=INPUT_DIR,
                    output_folder=OUTPUT_DIR,
                    char_threshold=char_threshold,
                    tag_threshold=tag_threshold,
                    status_callback=update_status,
                    enable_ai=enable_ai 
                )
                
                # 3. Zip Results
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                zip_filename = f"Cleaned_TMX_{timestamp}.zip"
                zip_path = os.path.join(OUTPUT_DIR, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(OUTPUT_DIR):
                        for file in files:
                            if file != zip_filename:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, OUTPUT_DIR)
                                zipf.write(file_path, arcname=arcname)

                status_container.update(label="Cleaning Complete!", state="complete", expanded=True)
                
                # 7. Results Dashboard
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Files Scanned", files_scanned)
                col2.metric("Files Modified", files_cleaned)
                col3.metric("Segments Removed", tus_removed)

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