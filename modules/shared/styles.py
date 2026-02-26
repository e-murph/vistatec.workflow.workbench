import streamlit as st
import base64
import os

def get_base64_of_bin_file(bin_file):
    """
    Reads a binary file and converts it to base64 so CSS can use it.
    """
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def set_page_style(background_image_path=None, footer_image_path=None, logo_path="assets/logo.png"):
    """
    Injects CSS to set a background image, sticky footer, header styling, and sidebar color.
    Dynamically adapts to Light/Dark mode.
    """
    
    # --- 1. HANDLE SIDEBAR LOGO ---
    if logo_path and os.path.exists(logo_path):
        st.logo(logo_path, icon_image=logo_path) 

    # --- 2. CSS STYLING ---
    css = ""
    
    # 1. Handle Background Image
    if background_image_path and os.path.exists(background_image_path):
        bin_str = get_base64_of_bin_file(background_image_path)
        css += f'''
        <style>
            .stApp {{
                background-image: url("data:image/png;base64,{bin_str}");
                background-attachment: fixed;
                background-size: cover;
            }}
        </style>
        '''

    # 2. Handle Footer/Banner Image, Header, and Sidebar
    if footer_image_path and os.path.exists(footer_image_path):
        bin_str = get_base64_of_bin_file(footer_image_path)
        
        css += f'''
        <style>
            /* Create space at bottom so content isn't covered by footer */
            .main .block-container {{
                padding-bottom: 120px; 
            }}
            
            /* --- DEFAULT (LIGHT MODE) STYLES --- */
            
            /* The Fixed Footer */
            .footer-container {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 60px; 
                
                background-color: #ffffff; 
                background-image: url("data:image/png;base64,{bin_str}");
                background-size: contain;
                background-position: center;
                background-repeat: no-repeat;
                
                /* Z-Index 999 puts it BEHIND the sidebar (which is 1000) */
                z-index: 999;
                border-top: 2px solid #55565a;
                
                transition: left 0.3s ease, width 0.3s ease;
            }}
            
            /* Top Header */
            header[data-testid="stHeader"] {{
                background-color: #e5e5e7;
            }}
            
            /* Sidebar */
            section[data-testid="stSidebar"] {{
                background-color: #e5e5e7; 
                border-right: 2px solid #CFB62C;
            }}

            /* Ensure Sidebar sits on top of footer */
            [data-testid="stSidebar"] {{
                z-index: 1000;
            }}

            /* --- DARK MODE OVERRIDES --- */
            /* If the user is using Dark Mode, swap the hardcoded light colors for Streamlit variables */
            @media (prefers-color-scheme: dark) {{
                .footer-container {{
                    background-color: var(--background-color);
                    border-top: 2px solid #CFB62C; /* Change border to gold so it pops against dark mode */
                }}
                
                header[data-testid="stHeader"] {{
                    background-color: var(--background-color);
                }}
                
                section[data-testid="stSidebar"] {{
                    /* Uses Streamlit's native dark sidebar color */
                    background-color: var(--secondary-background-color);
                    border-right: 2px solid #CFB62C;
                }}
            }}
        </style>
        <div class="footer-container"></div>
        '''
    
    if css:
        st.markdown(css, unsafe_allow_html=True)