import streamlit as st

# API Configuration
API_KEY = st.secrets["OPENAI_API_KEY"]

# Chat Configuration
MAX_HISTORY = 10  # Nombre max de messages dans l'historique
STREAM_RESPONSE = True  # Si l'API supporte le streaming