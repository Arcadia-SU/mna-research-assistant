import streamlit as st
from services.auth_service import AuthService
from ui.auth_ui import show_login_form, show_error_page
from ui.main_ui import main_app_ui
from ui.styles import apply_base_styles
from utils.logger import setup_logger
from utils.exception_utils import format_exception

# Configuration du logging
logger = setup_logger()

# Configurer la page Streamlit
st.set_page_config(
    page_title="Assistant de Recherche M&A",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Appliquer les styles de base (masquer la barre latérale, etc.)
apply_base_styles()

# Initialiser les variables d'état d'authentification
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

def main():
    """Fonction principale de l'application."""
    try:
        # Initialiser le service d'authentification
        auth_service = AuthService()
        
        # Récupérer l'état d'authentification actuel
        authentication_status = st.session_state.get("authentication_status", None)
        
        # Si l'utilisateur n'est pas connecté, afficher le formulaire de connexion
        if not authentication_status:
            logger.info("Utilisateur non authentifié, affichage du formulaire de connexion")
            auth_success = show_login_form(auth_service)
            if not auth_success:
                st.stop()
        
        # Si l'authentification a réussi, afficher l'interface principale
        if authentication_status:
            logger.info(f"Utilisateur authentifié: {st.session_state.get('name')}")
            
            # Afficher l'interface principale
            main_app_ui()
            
            # Le bouton de déconnexion est maintenant intégré dans main_app_ui
            # donc nous n'avons plus besoin de l'appeler ici
    
    except Exception as e:
        logger.critical(f"Erreur critique dans l'application: {format_exception(e)}")
        show_error_page(f"Erreur critique: {str(e)}")
        st.exception(e)
        st.stop()

if __name__ == "__main__":
    main()
