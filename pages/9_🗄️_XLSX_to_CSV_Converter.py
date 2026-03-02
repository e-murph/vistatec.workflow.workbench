import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.converter.xlsx_to_csv_logic import process_xlsx_to_csv

# 1. Page Config
st.set_page_config(
    page_title="XLSX to CSV Converter", 
    page_icon="🗄️", 
    layout="wide"
)

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_light_path="assets/banner_light.png",
    footer_image_dark_path="assets/banner_dark.png"
)

# 2. Custom CSS
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    
    /* --- DEFAULT (LIGHT MODE) STYLES --- */
    h1 {color: #0056b3;}
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
    @media (prefers-color-scheme: dark) {
        h1 {color: #66b2ff;} 
        .stButton>button {
            background-color: #66b2ff;
            color: #000000; 
        }
        .streamlit-expanderHeader {
            color: #66b2ff;
        }
    }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_xlsx_input"): shutil.rmtree("temp_xlsx_input")
        if os.path.exists("temp_csv_output"): shutil.rmtree("temp_csv_output")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("🗄️ Batch XLSX to CSV Converter")

# A. Description
st.markdown("""
**Instantly convert bulk Excel files (.xlsx) to CSV format.** Upload a batch of Excel files, and the tool will parse them and package the resulting CSVs into a single ZIP file for download.
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Upload Files:** Drag and drop your batch of `.xlsx` files into the uploader below.
    2. **Process:** Click **Convert to CSV**.
    3. **Download:** Save the packaged ZIP file containing your new CSVs.
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. File Uploader
uploaded_files = st.file_uploader(
    "📂 Upload XLSX Files", 
    type=["xlsx"],
    accept_multiple_files=True
)

# 6. Processing Logic
if uploaded_files:
    if st.button("🚀 Convert to CSV", type="primary"):
        
        TEMP_INPUT = "temp_xlsx_input"
        TEMP_OUTPUT = "temp_csv_output"
        
        # Clean/Create Dirs
        if os.path.exists(TEMP_INPUT): shutil.rmtree(TEMP_INPUT)
        if os.path.exists(TEMP_OUTPUT): shutil.rmtree(TEMP_OUTPUT)
        os.makedirs(TEMP_INPUT, exist_ok=True)
        os.makedirs(TEMP_OUTPUT, exist_ok=True)
        
        success_count = 0
        fail_count = 0
        
        # Start Status Log
        with st.status("⚙️ Converting files...", expanded=True) as status:
            
            for uploaded_file in uploaded_files:
                status.update(label=f"Converting: {uploaded_file.name}...")
                
                # Save input
                input_path = os.path.join(TEMP_INPUT, uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Determine output path (.csv instead of .xlsx)
                base_name = os.path.splitext(uploaded_file.name)[0]
                output_path = os.path.join(TEMP_OUTPUT, f"{base_name}.csv")
                
                # Process file
                success, error_msg = process_xlsx_to_csv(input_path, output_path)
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    st.error(f"Failed to convert {uploaded_file.name}: {error_msg}")

            # Zip Results
            if success_count > 0:
                status.write("📦 Packaging CSVs...")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                zip_filename = f"Converted_CSVs_{timestamp}.zip"
                zip_path = os.path.join(TEMP_OUTPUT, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(TEMP_OUTPUT):
                        for file in files:
                            if file.endswith('.csv'):
                                file_path = os.path.join(root, file)
                                zipf.write(file_path, arcname=file)

                status.update(label="✅ Conversion Complete!", state="complete", expanded=True)

                # 7. Results Dashboard
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Files Uploaded", len(uploaded_files))
                col2.metric("Successfully Converted", success_count)
                col3.metric("Failed", fail_count)

                with open(zip_path, "rb") as fp:
                    st.download_button(
                        label="📥 Download Converted CSVs (ZIP)",
                        data=fp,
                        file_name=zip_filename,
                        mime="application/zip",
                        use_container_width=True
                    )
            else:
                status.update(label="❌ Conversion Failed", state="error", expanded=True)
                st.error("No files were successfully converted.")