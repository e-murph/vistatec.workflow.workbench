import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.tmx.multilingual_tmx_logic import process_multilingual_tmx

st.set_page_config(page_title="Multilingual TMX Splitter", page_icon="🌍", layout="wide")

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
        1. Upload a **Multilingual TMX** file.
        2. The tool detects all language pairs.
        3. It generates separate **TMX** and **CSV** files for each pair.
        4. Download the combined ZIP package.
        """
    )
    st.markdown("---")
    
    # Clear Temp Files Button
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_multi_input"): shutil.rmtree("temp_multi_input")
        if os.path.exists("temp_multi_output"): shutil.rmtree("temp_multi_output")
        st.success("Temp folders cleared.")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© Vistatec 2026")

# 4. Main Content
st.title("🌍 Multilingual TMX Splitter")
st.markdown("""
Extracts specific language pairs from large multilingual TMX files.
**Outputs:** Individual TMX and CSV files for every unique source/target pair found in the master file.
""")
st.warning("⚠️ CONFIDENTIAL: For Internal Vistatec Use Only.")

# File Uploader
uploaded_file = st.file_uploader("Upload Multilingual TMX", type=["tmx"])

if st.button("Split TMX") and uploaded_file:
    
    # Setup Temp Folders
    TEMP_INPUT = "temp_multi_input"
    TEMP_OUTPUT = "temp_multi_output"
    
    # Clean previous run
    if os.path.exists(TEMP_INPUT): shutil.rmtree(TEMP_INPUT)
    if os.path.exists(TEMP_OUTPUT): shutil.rmtree(TEMP_OUTPUT)
    
    os.makedirs(TEMP_INPUT, exist_ok=True)
    os.makedirs(TEMP_OUTPUT, exist_ok=True)
    
    status_container = st.status("Processing...", expanded=True)
    
    try:
        # A. Save uploaded file
        status_container.write("📂 Saving uploaded file...")
        input_path = os.path.join(TEMP_INPUT, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # B. Define Status Callback
        def update_status_msg(msg):
            status_container.write(f"⚙️ {msg}")

        # C. Run Logic
        tu_count, pair_count = process_multilingual_tmx(
            file_path=input_path,
            output_dir=TEMP_OUTPUT,
            status_callback=update_status_msg
        )
        
        status_container.update(label="Processing Complete!", state="complete", expanded=False)
        st.success(f"✅ Success! Processed {tu_count} segments across {pair_count} language pairs.")

        # D. Zip and Download
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        zip_filename = f"Split_TMX_Package_{timestamp}.zip"
        zip_path = os.path.join(TEMP_OUTPUT, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(TEMP_OUTPUT):
                for file in files:
                    if file != zip_filename:
                        zipf.write(os.path.join(root, file), arcname=file)

        with open(zip_path, "rb") as fp:
            st.download_button(
                label="📦 Download Split Files (ZIP)",
                data=fp,
                file_name=zip_filename,
                mime="application/zip",
                use_container_width=True
            )

    except Exception as e:
        status_container.update(label="Error", state="error")
        st.error(f"An error occurred: {str(e)}")
        
    finally:
        # Optional Cleanup
        pass