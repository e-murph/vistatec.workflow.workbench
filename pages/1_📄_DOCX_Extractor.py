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

# 2. Custom CSS (Kept your existing style adjustments)
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    h1 {color: #0056b3;}
    .stButton>button {
        width: 100%;
        background-color: #0056b3;
        color: white;
    }
    /* Add a subtle border to the instructions expander */
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #0056b3;
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
    2. **Process:** The system will automatically scan for added/deleted text.
    3. **Review:** Status indicator for progress.
    4. **Download:** Click the button to save the **Master Report**.
    """)

st.warning("⚠️ **CONFIDENTIAL:** For Internal Vistatec Use Only.")
st.markdown("---")

# 5. File Uploader
uploaded_files = st.file_uploader(
    "📂 Upload DOCX Files",
    type="docx",
    accept_multiple_files=True,
    help="Limit 200MB per file."
)

if uploaded_files:
    os.makedirs("temp_upload", exist_ok=True)
    all_changes = []

    # 6. Modern Status Container (Replaces simple progress bar)
    # This creates a visually pleasing 'log' that collapses when done
    with st.status("🚀 Processing documents...", expanded=True) as status:
        
        for i, uploaded_file in enumerate(uploaded_files):
            # Update status label
            status.update(label=f"Scanning: {uploaded_file.name}...")
            
            # Save temp file
            temp_path = os.path.join("temp_upload", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Process logic
            file_changes = extract_sentence_diffs(temp_path)

            # Add filename to tuple
            for original, edited, html in file_changes:
                all_changes.append((uploaded_file.name, original, edited, html))
                
        # Mark as complete
        status.update(label="✅ Processing Complete!", state="complete", expanded=False)

    # 7. Results Dashboard
    st.markdown("---")
    
    if all_changes:
        # Metrics Row - Gives a professional "Dashboard" feel
        col1, col2 = st.columns(2)
        col1.metric("Documents Scanned", len(uploaded_files))
        col2.metric("Total Changes Found", len(all_changes))

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