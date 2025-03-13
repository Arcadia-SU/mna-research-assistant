"""
Styles CSS pour l'application Streamlit.
"""

def apply_base_styles():
    """Applique les styles de base et masque la barre latérale."""
    import streamlit as st
    
    # Masquer le menu hamburger et la barre latérale
    hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        .css-1544g2n {padding-top: 0rem;}
        </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

def apply_chat_styles():
    """Applique les styles pour l'interface de chat."""
    import streamlit as st
    
    # CSS personnalisé pour un design minimaliste
    st.markdown("""
    <style>
    .app-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 0.8rem;
    }
    .title-container {
        display: flex;
        justify-content: center;
        margin-bottom: 1.5rem;
    }
    .stTextInput>div>div>input {
        color: #333;
        background-color: white;
        border-radius: 5px;
        border: 1px solid #ddd;
        padding: 10px 15px;
    }
    </style>
    """, unsafe_allow_html=True)
