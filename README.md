---

# 🏢 Vistatec Internal Utility Hub

A centralized, secure Streamlit dashboard hosting multiple internal utility tools for Vistatec employees.
**Secured by Azure AD.**

---

## 🛠️ Included Tools

| Tool | Description | Inputs | Outputs |
| --- | --- | --- | --- |
| **📄 DOCX Extractor** | Extracts tracked changes from contracts & reports. | `.docx` | HTML Report |
| **📊 Phrase Converter** | Converts Phrase TMS CSV analysis files into formatted Excel reports. | `.csv` | ZIP (4x Excel files) |
| **🔗 TMX Aligner** | Combines two TMX files by pivoting through a common language (e.g., DE->EN + DE->FR = EN->FR). | `.tmx` | TMX + Reports |
| **🧹 Flare Cleaner** | Cleans MadCap Flare files and fixes errors caused by XTM filters. | `.html`, `.fltoc` | Cleaned Files (ZIP) |
| **🌍 Multilingual Splitter** | Splits large multilingual TMX files into individual language pair TMX/CSV files. | `.tmx` | ZIP (Pairs) |
| **🔐 Password Generator** | Generates cryptographically secure passwords locally using Python's `secrets` module. | User Settings | Text / CSV |

---

## 📂 Project Structure

The project follows a modular architecture to keep logic separated from the UI.

```text
extract_track_changes/
├── 0_🏠_Home.py                  # Entry Point (Landing Page)
├── pages/                        # Streamlit Pages (One file per tool)
│   ├── 1_📄_DOCX_Extractor.py
│   ├── 2_📊_Phrase_Converter.py
│   ├── 3_🔗_TMX_Aligner.py
│   ├── 4_🧹_Flare_Cleaner.py
│   ├── 5_🌍_Multilingual_Splitter.py
│   └── 6_🔐_Password_Generator.py
├── modules/                      # Core Logic Packages
│   ├── docx/                     # Logic for Tool 1
│   ├── phrase/                   # Logic for Tool 2
│   ├── tmx/                      # Logic for Tools 3 & 5
│   ├── flare/                    # Logic for Tool 4 (contains settings/)
│   ├── password/                 # Logic for Tool 6
│   └── shared/                   # Shared UI styles & helpers
├── assets/                       # Static assets (Logos, Banners)
├── requirements.txt              # Python Dependencies
└── README.md                     # Documentation

```

---

## 🚀 Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Vistatec/extract_track_changes.git
cd extract_track_changes

```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Run the App

```bash
streamlit run 0_🏠_Home.py

```

The app will open in your browser at `http://localhost:8501`.

---

## ☁️ Deployment (Azure App Service)

This app is designed to run on **Azure App Service** (Linux/Python).

### Configuration Settings

Ensure the following settings are configured in the Azure Portal:

1. **Startup Command:**
```bash
python -m streamlit run 0_🏠_Home.py --server.port 8000 --server.address 0.0.0.0

```


2. **Environment Variables:**
* `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`
* `WEBSITE_PORT` = `8000`



### Security (Azure AD)

Authentication is handled via **Azure App Service Authentication (Easy Auth)**.

* The app assumes it sits behind Azure AD.
* No internal auth logic is required in the Python code itself.

---

## 🧩 Modifying & Adding Tools

### Adding a New Tool

1. Create a new folder in `modules/` for your logic (e.g., `modules/pdf_tool/`).
2. Add your processing scripts inside that folder.
3. Create a new file in `pages/` (e.g., `7_📑_PDF_Merger.py`).
4. Import your logic: `from modules.pdf_tool import merger`.
5. Add `set_page_style()` to the top of the page for consistent branding.

### Updating Flare Cleaner Settings

The Flare Cleaner uses JSON configuration files found in:
`modules/flare/settings/`

* `language_replacements.json`
* `entity_replacements.json`
* `madcapdropdown_fix.json`

Modify these files to update the cleaning rules.

---

## 📄 License

**© Vistatec 2026**
Internal Utility Tool - Confidential.
```