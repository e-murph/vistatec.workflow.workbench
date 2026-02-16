import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.phrase.processor import process_csv

st.set_page_config(
    page_title="Phrase Report Converter",
    page_icon="📊",
    layout="wide"
)

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_path="assets/banner.png"
)

# 2. Custom CSS
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
        1. Upload **multiple** Phrase Analysis CSV files.
        2. Click 'Process Files' to convert them.
        3. Download the **ZIP Package** containing Excel reports.
        """
    )
    st.markdown("---")
    
    # Clear Temp Files Button
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_csv_input"): shutil.rmtree("temp_csv_input")
        if os.path.exists("temp_excel_output"): shutil.rmtree("temp_excel_output")
        st.success("Temp folders cleared.")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© Vistatec 2026")

# 4. Main Content
st.title("📊 Phrase CSV to Excel Converter")
st.markdown("""
Convert Phrase TMS CSV analysis files into formatted Excel reports with charts.
**Outputs 4 files per CSV:** * Full Report (with & without charts)
* No-Characters Report (with & without charts)
""")
st.warning("⚠️ CONFIDENTIAL: For Internal Vistatec Use Only.")

# File Uploader
uploaded_files = st.file_uploader(
    "Upload Phrase Analysis CSV(s)", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    INPUT_DIR = "temp_csv_input"
    OUTPUT_DIR = "temp_excel_output"
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if st.button(f"Process {len(uploaded_files)} File(s)"):
        
        progress_bar = st.progress(0, text="Starting processing...")
        
        try:
            for i, uploaded_file in enumerate(uploaded_files):
                input_path = os.path.join(INPUT_DIR, uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                progress_bar.progress((i) / len(uploaded_files), text=f"Processing {uploaded_file.name}...")
                process_csv(input_path, OUTPUT_DIR)

            progress_bar.progress(1.0, text="Creating Download Package...")

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            zip_filename = f"Processed_Reports_{timestamp}.zip"
            zip_path = os.path.join(OUTPUT_DIR, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(OUTPUT_DIR):
                    for file in files:
                        if file != zip_filename:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, arcname=file)

            with open(zip_path, "rb") as fp:
                st.success(f"✅ Success! Processed {len(uploaded_files)} CSVs into Excel reports.")
                st.download_button(
                    label="📦 Download All Reports (ZIP)",
                    data=fp,
                    file_name=zip_filename,
                    mime="application/zip",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")