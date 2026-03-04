import streamlit as st
import os
import shutil
from datetime import datetime
from modules.docx.docx_logic import extract_sentence_diffs, create_html_report
from modules.shared.styles import set_page_style
from modules.docx.ai_summarizer import generate_executive_summary

# 1. Page Config
st.set_page_config(
    page_title="DOCX Track Changes Extractor",
    page_icon="📄",
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

# 3. Sidebar (Cleaned up for "Admin" tasks only)
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Clear Temp Files Button
    if st.button("🚮 Clear Temp Files"):
        if os.path.exists("temp_upload"):
            shutil.rmtree("temp_upload")
        st.toast("Temporary files cleared successfully!", icon="🧹")
        
    st.markdown("---")
    st.caption("🔒 Secured by Azure AD")
    st.caption("© 2026 Vistatec, Ltd.")

# 4. Main Content Area
st.title("📄 DOCX Track Changes Extractor")

# --- NEW LAYOUT SECTION ---
# A. Description
st.markdown("""
**Securely extract and review tracked changes from DOCX files.** This tool scans multiple Word documents, extracts text marked as 'Tracked Changes', 
and consolidates them into a single HTML report for easy auditing.
""")

# B. Instructions (Using an Expander to keep UI clean)
with st.expander("ℹ️ How to use this tool", expanded=True):
    st.markdown("""
    1. **Upload Files:** Drag and drop your `.docx` files into the uploader below.
    2. **Process:** Click the **Extract Tracked Changes** button.
    3. **Review:** Status indicator for progress.
    4. **Download:** Click the button to save the **Master Report**.
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. File Uploader & Controls
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_files = st.file_uploader(
        "📂 Upload DOCX Files",
        type="docx",
        accept_multiple_files=True,
        help="Limit 200MB per file."
    )
with col2:
    st.write("<br>", unsafe_allow_html=True) # Spacer
    enable_ai = st.toggle("✨ Enable AI Summary", help="Uses Gemini to summarize substantive changes.")
    
    # --- DYNAMIC AI WARNING ---
    if enable_ai:
        st.markdown("""
        <div style="font-size: 0.8em; color: #666; margin-top: 10px; line-height: 1.2;">
            🤖 <b>Note:</b> Gemini is AI and can make mistakes. Please review all AI outputs manually.<br>
            <a href="https://support.google.com/gemini/answer/13594961" target="_blank">Your privacy & Gemini</a>
        </div>
        """, unsafe_allow_html=True)

# 6. Processing Logic
if uploaded_files:
    # --- THIS IS THE NEW BUTTON ---
    if st.button("🚀 Extract Tracked Changes", type="primary"):
        
        os.makedirs("temp_upload", exist_ok=True)
        all_changes = []

        # Modern Status Container
        with st.status("⚙️ Processing documents...", expanded=True) as status:
            
            for i, uploaded_file in enumerate(uploaded_files):
                status.update(label=f"Scanning: {uploaded_file.name}...")
            
                temp_path = os.path.join("temp_upload", uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                file_changes = extract_sentence_diffs(temp_path)

                for original, edited, html in file_changes:
                    all_changes.append((uploaded_file.name, original, edited, html))
                
            status.update(label="✅ Extraction Complete!", state="complete", expanded=False)

        # 7. Results Dashboard
        st.markdown("---")
        
        if all_changes:
            col1, col2 = st.columns(2)
            col1.metric("Documents Scanned", len(uploaded_files))
            col2.metric("Total Changes Found", len(all_changes))

            # --- NEW AI SUMMARY DISPLAY ---
            if enable_ai:
                st.markdown("### ✨ AI Executive Summary")
                with st.spinner("🤖 Analyzing changes..."):
                    ai_summary = generate_executive_summary(all_changes)
                    st.info(ai_summary)
            # ------------------------------

            # Generate Report
            report_html = create_html_report(all_changes)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            file_name = f"Master_Report_{timestamp}.html"

            # Download Button
            st.download_button(
                label="📥 Download Master Report",
                data=report_html,
                file_name=file_name,
                mime="text/html",
                use_container_width=True
            )
        else:
            st.info(f"✅ Scanned {len(uploaded_files)} files, but no tracked changes were found.")