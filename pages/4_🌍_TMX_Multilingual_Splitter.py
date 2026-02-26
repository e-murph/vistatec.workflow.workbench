import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.tmx.multilingual_tmx_logic import process_multilingual_tmx

# 1. Page Config
st.set_page_config(
    page_title="Multilingual TMX Splitter", 
    page_icon="🌍", 
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
        if os.path.exists("temp_multi_input"): shutil.rmtree("temp_multi_input")
        if os.path.exists("temp_multi_output"): shutil.rmtree("temp_multi_output")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("🌍 Multilingual TMX Splitter")

# --- NEW LAYOUT SECTION ---
# A. Description
st.markdown("""
**Extract specific language pairs from large multilingual TMX files.** This tool scans a single TMX containing multiple languages and automatically splits it into individual TMX and CSV files for every unique source/target pair found.
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Upload File:** Select a Multilingual TMX file.
    2. **Process:** Click **Split TMX** to begin extraction.
    3. **Review:** The tool will list every language pair detected.
    4. **Download:** Get a ZIP package containing all the separated files.
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. File Uploader
uploaded_file = st.file_uploader(
    "📂 Upload Multilingual TMX", 
    type=["tmx"],
    help="Upload a TMX file containing 3+ languages."
)

# 6. Processing Logic
if uploaded_file:
    
    # Action Button
    if st.button("🚀 Split TMX", type="primary"):
        
        # Define Dirs
        TEMP_INPUT = "temp_multi_input"
        TEMP_OUTPUT = "temp_multi_output"
        
        # Clean/Create Dirs
        if os.path.exists(TEMP_INPUT): shutil.rmtree(TEMP_INPUT)
        if os.path.exists(TEMP_OUTPUT): shutil.rmtree(TEMP_OUTPUT)
        os.makedirs(TEMP_INPUT, exist_ok=True)
        os.makedirs(TEMP_OUTPUT, exist_ok=True)
        
        # Start Status Log
        with st.status("⚙️ Analyzing TMX structure...", expanded=True) as status:
            try:
                # A. Save File
                status.write("📂 Saving uploaded file...")
                input_path = os.path.join(TEMP_INPUT, uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # B. Define Status Callback
                def update_status_msg(msg):
                    status.write(f"⚙️ {msg}")

                # C. Run Logic
                # The logic function returns (total_tus, total_pairs)
                # It automatically writes files to output_dir
                tu_count, pair_count = process_multilingual_tmx(
                    file_path=input_path,
                    output_dir=TEMP_OUTPUT,
                    status_callback=update_status_msg
                )
                
                # D. Zip Results
                status.write("📦 Packaging separated files...")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                zip_filename = f"Split_TMX_{timestamp}.zip"
                zip_path = os.path.join(TEMP_OUTPUT, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(TEMP_OUTPUT):
                        for file in files:
                            if file != zip_filename:
                                zipf.write(os.path.join(root, file), arcname=file)

                status.update(label="✅ Splitting Complete!", state="complete", expanded=True)

                # 7. Results Dashboard
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                col1.metric("Total Segments Scanned", tu_count)
                col2.metric("Language Pairs Created", pair_count)

                with open(zip_path, "rb") as fp:
                    st.download_button(
                        label="📥 Download Split Package (ZIP)",
                        data=fp,
                        file_name=zip_filename,
                        mime="application/zip",
                        use_container_width=True
                    )

            except Exception as e:
                status.update(label="Processing Failed", state="error")
                st.error(f"An error occurred: {str(e)}")