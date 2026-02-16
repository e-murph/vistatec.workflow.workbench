import streamlit as st
import os
import shutil
from datetime import datetime
from modules.docx.docx_logic import extract_sentence_diffs, create_html_report
from modules.shared.styles import set_page_style

# 1. Page Config
st.set_page_config(
    page_title="DOCX Track Changes Extractor",
    page_icon="📄",
    layout="wide"
)

# --- APPLY STYLING ---
set_page_style(
    background_image_path="assets/background.jpg",
    footer_image_path="assets/banner.png"
)
# ---------------------------

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
        1. Upload **multiple** DOCX files containing tracked changes.
        2. Wait for the processing bar to finish.
        3. Download the **Master Report** HTML file.
        4. Open the report in Edge/Chrome to review changes.
        """
    )
    st.markdown("---")
    
    # Clear Temp Files Button
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_upload"):
            shutil.rmtree("temp_upload")
        st.success("Temp folders cleared.")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© Vistatec 2026")

# 4. Main Content Area (Left Aligned)
st.title("📄 DOCX Track Changes Extractor")
st.markdown("""Securely extract and review tracked changes.""")
st.warning("⚠️ CONFIDENTIAL: For Internal Vistatec Use Only.")

# Divider
st.markdown("---")

uploaded_files = st.file_uploader(
    "Drop your files here",
    type="docx",
    accept_multiple_files=True
)

if uploaded_files:
    # Use a temporary directory
    os.makedirs("temp_upload", exist_ok=True)

    all_changes = []

    # UI: Clean Progress Bar
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)

    for i, uploaded_file in enumerate(uploaded_files):
        # Save temp file
        temp_path = os.path.join("temp_upload", uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Process logic
        file_changes = extract_sentence_diffs(temp_path)

        # Add filename to tuple
        for original, edited, html in file_changes:
            all_changes.append((uploaded_file.name, original, edited, html))

        # Update progress
        my_bar.progress((i + 1) / len(uploaded_files), text=f"Processed {uploaded_file.name}")

    my_bar.empty()  # Remove progress bar when done
    st.markdown("---")

    if all_changes:
        report_html = create_html_report(all_changes)

        st.success(f"✅ Success! Found {len(all_changes)} changes across {len(uploaded_files)} documents.")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        file_name_with_time = f"Confidential_Master_Report_{timestamp}.html"

        # Big Download Button
        st.download_button(
            label="📥 Download Master Report",
            data=report_html,
            file_name=file_name_with_time,
            mime="text/html",
            use_container_width=True
        )
    else:
        st.info("✅ Processing complete, but no tracked changes were found.")