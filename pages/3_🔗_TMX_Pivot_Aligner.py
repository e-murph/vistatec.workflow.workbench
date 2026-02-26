import streamlit as st
import os
import shutil
import zipfile
from datetime import datetime
from modules.tmx.tmx_processor import parse_tmx, detect_lang_codes_set, create_pivot_tmx
from modules.tmx.config import LANGUAGES, NORMALIZED_CODES
from modules.shared.styles import set_page_style

# 1. Page Config
st.set_page_config(
    page_title="TMX Pivot Aligner", 
    page_icon="🔗", 
    layout="wide"
)

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_path="assets/banner.png"
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
        if os.path.exists("temp_tmx_processing"): shutil.rmtree("temp_tmx_processing")
        if os.path.exists("temp_tmx_output"): shutil.rmtree("temp_tmx_output")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("🔗 TMX Pivot Aligner")

# --- NEW LAYOUT SECTION ---
# A. Description
st.markdown("""
**Combine two TMX files by pivoting through a common language.**
This tool merges two separate Translation Memories (e.g., *German->English* and *German->French*) to create a new direct translation pair (*English->French*).
""")

# B. Instructions
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Upload Source TMX:** This is your 'Pivot' file (e.g., DE -> EN).
    2. **Upload Target TMX:** This is your 'Target' file (e.g., DE -> FR).
    3. **Select Output Language:** Choose the language you want to map **TO** (e.g., English).
    4. **Process:** Click **Align TMX Files** to generate the new TMX (e.g., EN -> FR).
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. UI Setup (Inputs)
col1, col2 = st.columns(2)

with col1:
    source_file = st.file_uploader("📂 Upload Source TMX (Pivot)", type=["tmx"], help="Example: DE-EN file")

with col2:
    target_file = st.file_uploader("📂 Upload Target TMX", type=["tmx"], help="Example: DE-FR file")

language_names = sorted(LANGUAGES.keys())
selected_lang_name = st.selectbox(
    "🎯 Select Output Source Language (The language you want to map TO)",
    options=language_names,
    index=language_names.index("English (US)") if "English (US)" in language_names else 0
)

# 6. Processing Logic
if st.button("🚀 Align TMX Files", type="primary"):
    
    if not source_file or not target_file:
        st.error("❌ Please upload both Source and Target TMX files.")
    else:
        # Define Dirs
        TEMP_DIR = "temp_tmx_processing"
        OUTPUT_DIR = "temp_tmx_output"
        
        if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
        if os.path.exists(OUTPUT_DIR): shutil.rmtree(OUTPUT_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Start Status Log
        with st.status("⚙️ Starting Alignment...", expanded=True) as status:
            try:
                # A. Save Files
                status.write("📂 Saving uploaded files...")
                src_path = os.path.join(TEMP_DIR, source_file.name)
                tgt_path = os.path.join(TEMP_DIR, target_file.name)
                
                with open(src_path, "wb") as f:
                    f.write(source_file.getbuffer())
                with open(tgt_path, "wb") as f:
                    f.write(target_file.getbuffer())

                # B. Parse & Analyze
                status.write("🔍 Analyzing language codes...")
                pivot_root = parse_tmx(src_path)
                target_root = parse_tmx(tgt_path)

                pivot_langs = detect_lang_codes_set(pivot_root)
                target_langs = detect_lang_codes_set(target_root)

                # C. Validation Logic
                common = pivot_langs & target_langs
                
                if len(common) != 1:
                    status.update(label="Validation Error", state="error")
                    st.error(f"❌ Files must share EXACTLY one common language. Found: {common}")
                    st.stop()

                pivot_source_lang = list(common)[0]

                if len(pivot_langs) != 2 or len(target_langs) != 2:
                    status.update(label="Validation Error", state="error")
                    st.error("❌ Each TMX file must contain exactly two languages.")
                    st.stop()

                pivot_target_lang = list(pivot_langs - common)[0]
                input_target_lang = list(target_langs - common)[0]

                # Check User Selection
                expected_output_code = LANGUAGES[selected_lang_name]
                normalized_pivot = NORMALIZED_CODES.get(pivot_target_lang.lower(), pivot_target_lang)

                if normalized_pivot != expected_output_code:
                    status.update(label="Language Mismatch", state="error")
                    st.error(f"❌ Mismatch: Source TMX target is '{pivot_target_lang}', but you selected '{selected_lang_name}' ({expected_output_code}).")
                    st.stop()

                output_source_lang = expected_output_code
                normalized_target = NORMALIZED_CODES.get(input_target_lang.lower(), input_target_lang)
                output_target_lang = normalized_target

                # D. Run Alignment
                status.write("🔗 Matching segments (Fuzzy Match)...")
                
                out_filename = f"{output_source_lang}_{output_target_lang}.tmx"
                out_path = os.path.join(OUTPUT_DIR, out_filename)

                create_pivot_tmx(
                    pivot_root, target_root, out_path, 
                    tgt_path, output_target_lang, input_target_lang, 
                    pivot_target_lang, pivot_source_lang, output_source_lang, 
                    src_path
                )

                # E. Zip Results
                status.write("📦 Packaging results...")
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                zip_filename = f"Aligned_TMX_{timestamp}.zip"
                zip_path = os.path.join(OUTPUT_DIR, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(OUTPUT_DIR):
                        for file in files:
                            if file != zip_filename:
                                zipf.write(os.path.join(root, file), arcname=file)

                status.update(label="✅ Alignment Complete!", state="complete", expanded=False)

                # 7. Results Dashboard
                st.markdown("---")
                col1, col2 = st.columns(2)
                col1.success("TMX Generated Successfully")
                
                with open(zip_path, "rb") as fp:
                    col2.download_button(
                        label="📥 Download TMX Package",
                        data=fp,
                        file_name=zip_filename,
                        mime="application/zip",
                        use_container_width=True
                    )

            except Exception as e:
                status.update(label="Processing Failed", state="error")
                st.error(f"An error occurred: {str(e)}")