import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.shared.styles import set_page_style
from modules.termweb.termweb_logic import parse_xml_to_xlsx

# 1. Page Config
st.set_page_config(
    page_title="TermWeb QA Converter", 
    page_icon="📝", 
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
        if os.path.exists("temp_termweb_input"): shutil.rmtree("temp_termweb_input")
        if os.path.exists("temp_termweb_output"): shutil.rmtree("temp_termweb_output")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("📝 TermWeb XML to Excel QA Converter")

# A. Description
st.markdown("""
**Convert TermWeb XML files into actionable Excel QA reports.** This tool aligns source and target terms, scores accuracy using a lexical matching algorithm, and generates up to 6 distinct filtered Excel reports for review.
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Upload Files:** Drop your TermWeb `.xml` files into the uploader below.
    2. **Process:** Click the **Generate QA Reports** button.
    3. **Download:** Save a ZIP file containing the formatted Excel reports (Full, Preferred Only, Perfect Matches, Missing Targets, etc.).
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. File Uploader & AI Toggle
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_files = st.file_uploader(
        "📂 Upload TermWeb XML Files", 
        type=["xml"],
        accept_multiple_files=True
    )
with col2:
    st.write("<br>", unsafe_allow_html=True) # Spacer to align the toggle with the uploader
    enable_ai = st.toggle("✨ Enable AI Semantic Review", help="Uses Gemini to check synonym validity and generate definitions.")
    
    # --- NEW DYNAMIC AI WARNING ---
    if enable_ai:
        st.markdown("""
        <div style="font-size: 0.8em; color: #666; margin-top: 10px; line-height: 1.2;">
            🤖 <b>Note:</b> Gemini is AI and can make mistakes. Please review all AI outputs manually.<br>
            <a href="https://support.google.com/gemini/answer/13594961" target="_blank">Your privacy & Gemini</a>
        </div>
        """, unsafe_allow_html=True)

# 6. Processing Logic
if uploaded_files:
    if st.button("🚀 Generate QA Reports", type="primary"):
        
        TEMP_INPUT = "temp_termweb_input"
        TEMP_OUTPUT = "temp_termweb_output"
        
        # Clean/Create Dirs
        if os.path.exists(TEMP_INPUT): shutil.rmtree(TEMP_INPUT)
        if os.path.exists(TEMP_OUTPUT): shutil.rmtree(TEMP_OUTPUT)
        os.makedirs(TEMP_INPUT, exist_ok=True)
        os.makedirs(TEMP_OUTPUT, exist_ok=True)
        
        # Start Status Log
        with st.status("⚙️ Processing TermWeb files...", expanded=True) as status:
            try:
                for uploaded_file in uploaded_files:
                    status.update(label=f"Analyzing: {uploaded_file.name}...")
                    
                    # Save input
                    input_path = os.path.join(TEMP_INPUT, uploaded_file.name)
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process file (generates multiple XLSX files in TEMP_OUTPUT)
                    # --- AI FLAG ADDED HERE ---
                    parse_xml_to_xlsx(input_path, TEMP_OUTPUT, enable_ai=enable_ai)

                # Zip Results
                status.write("📦 Packaging Excel reports...")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                zip_filename = f"TermWeb_QA_Reports_{timestamp}.zip"
                zip_path = os.path.join(TEMP_OUTPUT, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(TEMP_OUTPUT):
                        for file in files:
                            if file != zip_filename:
                                file_path = os.path.join(root, file)
                                zipf.write(file_path, arcname=file)

                status.update(label="✅ QA Reports Generated!", state="complete", expanded=True)

                # 7. Results Dashboard
                st.markdown("---")
                
                # Count total number of excel files generated
                generated_files = [f for f in os.listdir(TEMP_OUTPUT) if f.endswith('.xlsx')]
                
                col1, col2 = st.columns(2)
                col1.metric("XML Files Processed", len(uploaded_files))
                col2.metric("Excel Reports Created", len(generated_files))

                with open(zip_path, "rb") as fp:
                    st.download_button(
                        label="📥 Download Excel Reports (ZIP)",
                        data=fp,
                        file_name=zip_filename,
                        mime="application/zip",
                        use_container_width=True
                    )

            except Exception as e:
                status.update(label="Processing Failed", state="error")
                st.error(f"An error occurred: {str(e)}")