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

    # 2. Handle Footer/Banner Image
    if footer_image_path and os.path.exists(footer_image_path):
        bin_str = get_base64_of_bin_file(footer_image_path)
        css += f'''
        <style>
            /* Create space at bottom so content isn't covered by footer */
            .main .block-container {{
                padding-bottom: 120px; 
            }}
            
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
                
                left: 0;
                width: 100%;
            }}
            
            /* NOTE: Media Query removed. The footer now stays full width, 
               and the sidebar simply covers the left side of it. */

            /* Ensure Sidebar sits on top of footer */
            [data-testid="stSidebar"] {{
                z-index: 1000;
            }}
        </style>
        <div class="footer-container"></div>
        '''

    # 3. Handle Top Header Styling (NEW)
    # This targets the fixed header bar at the top of the page
        css += '''
        <style>
            /* Top Header: Transparent */
            header[data-testid="stHeader"] {
                /* Option A: Transparent (shows your background image) */
                /* background-color: rgba(0,0,0,0);
            
                /* Option B: Custom Color (e.g., White or Corporate Blue) */
                background-color: #e5e5e7; */
            }
            /* Sidebar: Custom Background Color */
            section[data-testid="stSidebar"] {
                background-color: #e5e5e7; /* Change this Hex Code to your preferred color */
            
                /* Optional: Add a border to separate it from the main content */
                border-right: 2px solid #CFB62C;
            }
        </style>
        '''
    
    if css:
        st.markdown(css, unsafe_allow_html=True)