import streamlit as st
import base64
import os

def get_base64_of_bin_file(bin_file):
    """Reads a binary file and converts it to base64 so CSS can use it."""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def set_page_style(background_image_path=None, footer_image_light_path=None, footer_image_dark_path=None, logo_path="assets/logo.png"):
    """
    Injects CSS to set a background image, sticky footer, header styling, and sidebar color.
    Dynamically swaps the footer banner based on Light/Dark mode.
    """
    
    # --- 1. HANDLE SIDEBAR LOGO ---
    if logo_path and os.path.exists(logo_path):
        st.logo(logo_path, icon_image=logo_path) 

    # --- 2. CSS STYLING ---
    css = ""
    
    # Convert images to base64 if they exist
    bg_b64 = get_base64_of_bin_file(background_image_path) if background_image_path and os.path.exists(background_image_path) else ""
    
    # Process both Light and Dark footers
    footer_light_b64 = get_base64_of_bin_file(footer_image_light_path) if footer_image_light_path and os.path.exists(footer_image_light_path) else ""
    footer_dark_b64 = get_base64_of_bin_file(footer_image_dark_path) if footer_image_dark_path and os.path.exists(footer_image_dark_path) else footer_light_b64 # Fallback to light if dark is missing

    css += f'''
    <style>
        /* --- DEFAULT (LIGHT MODE) --- */
        .stApp {{
            background-image: url("data:image/png;base64,{bg_b64}");
            background-attachment: fixed;
            background-size: cover;
        }}
        
        header[data-testid="stHeader"] {{
            background-color: #e5e5e7;
        }}
        
        section[data-testid="stSidebar"] {{
            background-color: #e5e5e7; 
            border-right: 2px solid #CFB62C;
        }}

        .main .block-container {{
            padding-bottom: 120px; 
        }}
        
        /* The Fixed Footer - Defaults to Light Banner */
        .footer-container {{
            position: fixed;
            bottom: 0; left: 0; width: 100%; height: 60px; 
            background-color: #ffffff; 
            background-image: url("data:image/png;base64,{footer_light_b64}");
            background-size: contain; 
            background-position: center; 
            background-repeat: no-repeat;
            z-index: 999;
            border-top: 2px solid #55565a;
        }}
        
        [data-testid="stSidebar"] {{
            z-index: 1000;
        }}

        /* --- DARK MODE OVERRIDES --- */
        @media (prefers-color-scheme: dark) {{
            /* Darken the main background image so white text is readable */
            .stApp {{
                background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), url("data:image/png;base64,{bg_b64}");
            }}
            
            header[data-testid="stHeader"] {{
                background-color: rgba(14, 17, 23, 0.9) !important;
            }}
            
            section[data-testid="stSidebar"] {{
                background-color: #0e1117 !important; 
                border-right: 2px solid #CFB62C !important;
            }}

            /* Swap the Footer to the Dark Banner */
            .footer-container {{
                background-color: #0e1117 !important;
                background-image: url("data:image/png;base64,{footer_dark_b64}") !important;
                border-top: 2px solid #CFB62C !important;
            }}
        }}
    </style>
    <div class="footer-container"></div>
    '''
    
    if css:
        st.markdown(css, unsafe_allow_html=True)