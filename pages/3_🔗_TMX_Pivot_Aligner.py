import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.tmx.tmx_processor import parse_tmx, detect_lang_codes_set, create_pivot_tmx
from modules.tmx.config import LANGUAGES, NORMALIZED_CODES
from modules.shared.styles import set_page_style

st.set_page_config(page_title="TMX Pivot Aligner", page_icon="🔗", layout="wide")

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
        1. Upload a **Source TMX** (Pivot file).
        2. Upload a **Target TMX**.
        3. Select the **Output Language**.
        4. Download the generated TMX & Reports.
        """
    )
    st.markdown("---")
    
    # Clear Temp Files Button
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_tmx_processing"): shutil.rmtree("temp_tmx_processing")
        if os.path.exists("temp_tmx_output"): shutil.rmtree("temp_tmx_output")
        st.success("Temp folders cleared.")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© Vistatec 2026")

# 4. Main Content
st.title("🔗 TMX Pivot Aligner")
st.markdown("""
Combine two TMX files by pivoting through a common language.
* **Example:** (German -> English) + (German -> French) = **English -> French**
""")
st.warning("⚠️ CONFIDENTIAL: For Internal Vistatec Use Only.")

# --- UI Setup ---
col1, col2 = st.columns(2)

with col1:
    source_file = st.file_uploader("Upload Source TMX (Pivot File)", type=["tmx"])

with col2:
    target_file = st.file_uploader("Upload Target TMX", type=["tmx"])

language_names = sorted(LANGUAGES.keys())
selected_lang_name = st.selectbox(
    "Select Output Source Language (The language you want to map TO)",
    options=language_names,
    index=language_names.index("English (US)") if "English (US)" in language_names else 0
)

# --- Processing Logic ---
if st.button("Align TMX Files") and source_file and target_file:
    
    TEMP_DIR = "temp_tmx_processing"
    OUTPUT_DIR = "temp_tmx_output"
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    status = st.status("Processing TMX files...", expanded=True)
    
    try:
        status.write("📂 Saving uploaded files...")
        src_path = os.path.join(TEMP_DIR, source_file.name)
        tgt_path = os.path.join(TEMP_DIR, target_file.name)
        
        with open(src_path, "wb") as f:
            f.write(source_file.getbuffer())
        with open(tgt_path, "wb") as f:
            f.write(target_file.getbuffer())

        status.write("🔍 Parsing XML structures...")
        pivot_root = parse_tmx(src_path)
        target_root = parse_tmx(tgt_path)

        pivot_langs = detect_lang_codes_set(pivot_root)
        target_langs = detect_lang_codes_set(target_root)

        status.write("📐 Validating Pivot Languages...")
        
        common = pivot_langs & target_langs
        
        if len(common) != 1:
            status.update(label="Validation Error", state="error")
            st.error(f"Error: Files must share EXACTLY one common language code. Found: {common}")
            st.stop()

        pivot_source_lang = list(common)[0]

        if len(pivot_langs) != 2 or len(target_langs) != 2:
            status.update(label="Validation Error", state="error")
            st.error("Error: Each TMX file must contain exactly two languages.")
            st.stop()

        pivot_target_lang = list(pivot_langs - common)[0]
        input_target_lang = list(target_langs - common)[0]

        expected_output_code = LANGUAGES[selected_lang_name]
        normalized_pivot = NORMALIZED_CODES.get(pivot_target_lang.lower(), pivot_target_lang)

        if normalized_pivot != expected_output_code:
            status.update(label="Language Mismatch", state="error")
            st.error(f"Mismatch: Source TMX target language is '{pivot_target_lang}', but you selected '{selected_lang_name}' ({expected_output_code}).")
            st.stop()

        output_source_lang = expected_output_code
        normalized_target = NORMALIZED_CODES.get(input_target_lang.lower(), input_target_lang)
        output_target_lang = normalized_target

        status.write("⚙️ Running Pivot Alignment (Fuzzy Matching)...")
        
        out_filename = f"{output_source_lang}_{output_target_lang}.tmx"
        out_path = os.path.join(OUTPUT_DIR, out_filename)

        create_pivot_tmx(
            pivot_root, target_root, out_path, 
            tgt_path, output_target_lang, input_target_lang, 
            pivot_target_lang, pivot_source_lang, output_source_lang, 
            src_path
        )

        status.update(label="Alignment Complete!", state="complete", expanded=False)
        st.success("✅ TMX Alignment Successful")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        zip_filename = f"Aligned_TMX_Package_{timestamp}.zip"
        zip_path = os.path.join(OUTPUT_DIR, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(OUTPUT_DIR):
                for file in files:
                    if file != zip_filename:
                        zipf.write(os.path.join(root, file), arcname=file)

        with open(zip_path, "rb") as fp:
            st.download_button(
                label="📦 Download TMX & Reports (ZIP)",
                data=fp,
                file_name=zip_filename,
                mime="application/zip",
                use_container_width=True
            )

    except Exception as e:
        status.update(label="Processing Failed", state="error")
        st.error(f"An error occurred: {str(e)}")