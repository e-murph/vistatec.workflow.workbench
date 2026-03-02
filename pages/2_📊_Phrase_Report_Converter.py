import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.phrase.processor import process_csv

# 1. Page Config
st.set_page_config(
    page_title="Phrase Report Converter",
    page_icon="📊",
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

# 3. Sidebar (Admin/Settings only)
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Clear Temp Files Button
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_csv_input"): shutil.rmtree("temp_csv_input")
        if os.path.exists("temp_excel_output"): shutil.rmtree("temp_excel_output")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("📊 Phrase CSV to Excel Converter")

# --- NEW LAYOUT SECTION ---
# A. Description
st.markdown("""
**Convert raw Phrase TMS analysis data into professional Excel reports.** This tool processes CSV exports, applies formatting, and generates charts automatically.
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Upload Files:** Select one or multiple Phrase Analysis `.csv` files.
    2. **Process:** Click the **Start Processing** button.
    3. **Review:** Status log runs as files are converted.
    4. **Download:** Save the final ZIP package containing all Excel reports.
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. File Uploader
uploaded_files = st.file_uploader(
    "📂 Upload Phrase Analysis CSV(s)", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    # Action Button
    if st.button("🚀 Start Processing", type="primary"):
        
        # Define Directories
        INPUT_DIR = "temp_csv_input"
        OUTPUT_DIR = "temp_excel_output"
        
        # Clean/Create Dirs
        if os.path.exists(INPUT_DIR): shutil.rmtree(INPUT_DIR)
        if os.path.exists(OUTPUT_DIR): shutil.rmtree(OUTPUT_DIR)
        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 6. Modern Status Container
        with st.status("⚙️ Converting files...", expanded=True) as status:
            
            # Save and Process Files
            for i, uploaded_file in enumerate(uploaded_files):
                status.update(label=f"Processing: {uploaded_file.name}...")
                
                # Save Input
                input_path = os.path.join(INPUT_DIR, uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Run Logic
                try:
                    process_csv(input_path, OUTPUT_DIR)
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {e}")

            # Zip Results
            status.update(label="📦 Packaging reports...", state="running")
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            zip_filename = f"Processed_Reports_{timestamp}.zip"
            zip_path = os.path.join(OUTPUT_DIR, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(OUTPUT_DIR):
                    for file in files:
                        if file != zip_filename:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, arcname=file)
            
            status.update(label="✅ Conversion Complete!", state="complete", expanded=True)

        # 7. Results Dashboard
        st.markdown("---")
        
        # Calculate output count (approx 4 files per input)
        total_outputs = len(uploaded_files) * 4
        
        col1, col2 = st.columns(2)
        col1.metric("CSVs Processed", len(uploaded_files))
        col2.metric("Excel Reports Generated", f"~{total_outputs}")

        with open(zip_path, "rb") as fp:
            st.download_button(
                label="📥 Download All Reports (ZIP)",
                data=fp,
                file_name=zip_filename,
                mime="application/zip",
                use_container_width=True
            )