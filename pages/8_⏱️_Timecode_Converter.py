import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.timecode.timecode_logic import process_docx, process_vtt

# 1. Page Config
st.set_page_config(
    page_title="Timecode Converter", 
    page_icon="⏱️", 
    layout="wide"
)

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_light_path="assets/banner_light.png",
    footer_image_dark_path="assets/banner_dark.png"
)

# 2. Custom CSS (Light/Dark Mode compatible)
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
        if os.path.exists("temp_timecode_input"): shutil.rmtree("temp_timecode_input")
        if os.path.exists("temp_timecode_output"): shutil.rmtree("temp_timecode_output")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("⏱️ Timecode Converter")

# A. Description
st.markdown("""
**Convert raw timecodes into readable (MM:SS) formats.** This tool scans subtitle files (`.vtt`) or transcripts (`.docx`), identifies raw decimal timecodes, and replaces them with a clean minute/second format.
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Upload Files:** Drop your `.docx` or `.vtt` files into the uploader below.
    2. **Process:** Click the **Convert Timecodes** button.
    3. **Download:** Download the ZIP package containing your updated files.
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. File Uploader
uploaded_files = st.file_uploader(
    "📂 Upload Files", 
    type=["docx", "vtt"],
    accept_multiple_files=True
)

# 6. Processing Logic
if uploaded_files:
    if st.button("🚀 Convert Timecodes", type="primary"):
        
        TEMP_INPUT = "temp_timecode_input"
        TEMP_OUTPUT = "temp_timecode_output"
        
        # Clean/Create Dirs
        if os.path.exists(TEMP_INPUT): shutil.rmtree(TEMP_INPUT)
        if os.path.exists(TEMP_OUTPUT): shutil.rmtree(TEMP_OUTPUT)
        os.makedirs(TEMP_INPUT, exist_ok=True)
        os.makedirs(OUTPUT_DIR := TEMP_OUTPUT, exist_ok=True)
        
        # Start Status Log
        with st.status("⚙️ Converting files...", expanded=True) as status:
            try:
                # Process files
                for uploaded_file in uploaded_files:
                    status.update(label=f"Processing: {uploaded_file.name}...")
                    
                    # Save input
                    input_path = os.path.join(TEMP_INPUT, uploaded_file.name)
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Determine output path
                    output_path = os.path.join(TEMP_OUTPUT, f"Converted_{uploaded_file.name}")
                    
                    # Route to correct processing function
                    if uploaded_file.name.endswith('.docx'):
                        process_docx(input_path, output_path)
                    elif uploaded_file.name.endswith('.vtt'):
                        process_vtt(input_path, output_path)

                # Zip Results
                status.write("📦 Packaging converted files...")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                zip_filename = f"Converted_Timecodes_{timestamp}.zip"
                zip_path = os.path.join(TEMP_OUTPUT, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(TEMP_OUTPUT):
                        for file in files:
                            if file != zip_filename:
                                file_path = os.path.join(root, file)
                                zipf.write(file_path, arcname=file)

                status.update(label="✅ Conversion Complete!", state="complete", expanded=True)

                # 7. Results Dashboard
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                col1.metric("Files Processed", len(uploaded_files))
                col2.success("Ready for Download")

                with open(zip_path, "rb") as fp:
                    st.download_button(
                        label="📥 Download Converted Files (ZIP)",
                        data=fp,
                        file_name=zip_filename,
                        mime="application/zip",
                        use_container_width=True
                    )

            except Exception as e:
                status.update(label="Processing Failed", state="error")
                st.error(f"An error occurred: {str(e)}")