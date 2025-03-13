import os
import streamlit as st
from utils.logger import setup_logger
from utils.exception_utils import format_exception

# Configuration du logging
logger = setup_logger("auth_ui")

def show_login_form(auth_service):
    """Affiche le formulaire de connexion et gère le processus de connexion.
    
    Args:
        auth_service: Instance de AuthService
        
    Returns:
        bool: True si l'authentification a réussi, False sinon
    """
    try:
        # Ajouter un peu d'espace au-dessus du formulaire
        st.markdown("<div style='margin-top: 15vh'></div>", unsafe_allow_html=True)
        
        # Afficher le logo ou le titre
        st.markdown("<h1 style='text-align: center;'>Assistant de Recherche M&A</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; margin-bottom: 30px;'>Veuillez vous connecter pour accéder à l'application</p>", unsafe_allow_html=True)
        
        # Tenter de se connecter
        try:
            auth_status, name, username = auth_service.login(location='main')
        except Exception as login_error:
            logger.error(f"Erreur spécifique lors de la connexion: {format_exception(login_error)}")
            
            # Vérifier si c'est une erreur d'autorisation
            error_str = str(login_error)
            if "User not authorized" in error_str:
                st.error("Erreur d'autorisation: Vous n'êtes pas autorisé à vous connecter. Une session est peut-être déjà active ailleurs.")
                
                # Proposer des solutions spécifiques
                st.info("Suggestions: \n- Attendez quelques minutes et réessayez \n- Vérifiez qu'une autre session n'est pas ouverte ailleurs \n- Contactez l'administrateur si le problème persiste")
                
                # Bouton pour vider les cookies et la session et redémarrer proprement
                if st.button("Recharger", type="primary", help="Vide les cookies et réinitialise votre session."):
                    # Supprimer le cookie d'authentification
                    js = """
                    <script>
                    function deleteAuthCookies() {
                        document.cookie.split(";").forEach(function(c) {
                            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
                        });
                        localStorage.clear();
                        sessionStorage.clear();
                        window.location.reload();
                    }
                    deleteAuthCookies();
                    </script>
                    """
                    st.markdown(js, unsafe_allow_html=True)
                    
                    # Également vider la session côté serveur
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    
                    # Rediriger vers la page d'accueil
                    st.rerun()
            else:
                # Autre type d'erreur
                st.error(f"Erreur de connexion: {str(login_error)}")
                
                # Bouton simple pour recharger la page
                if st.button("Réessayer", type="primary"):
                    st.rerun()
            
            return False
        
        # Vérifier le statut d'authentification
        auth_status = st.session_state.get("authentication_status", None)
        if auth_status is True:
            logger.info(f"Utilisateur authentifié avec succès: {st.session_state.get('name')}")
            return True
        elif auth_status is False:
            logger.warning("Tentative de connexion avec des identifiants incorrects")
            st.error("Identifiants incorrects")
            return False
        else:
            logger.info("Aucune tentative de connexion")
            return False
    
    except Exception as e:
        logger.error(f"Erreur dans l'affichage du formulaire de connexion: {format_exception(e)}")
        st.error(f"Erreur lors de l'affichage du formulaire de connexion: {str(e)}")
        
        # Ajouter un bouton pour réinitialiser la session
        if st.button("Réinitialiser la session", type="primary", help="Cliquez ici pour réinitialiser complètement votre session"):
            # Réinitialiser toutes les variables de session sauf celles essentielles
            keys_to_keep = ['_is_running', '_script_run_ctx']
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    try:
                        del st.session_state[key]
                    except:
                        pass
            
            # Forcer le rechargement de la page
            st.rerun()
            
        return False

def show_logout_button(auth_service):
    """Affiche le bouton de déconnexion de manière discrète.
    
    Args:
        auth_service: Instance de AuthService
    """
    # Utiliser un bouton avec une icône Material Design pour la déconnexion
    try:
        # Utiliser un bouton Streamlit avec l'icône logout de Material Design
        if st.button("", icon=":material/logout:", type="tertiary", help="Se déconnecter"):
            # Exécuter la déconnexion sans afficher un autre bouton
            auth_service.logout(location='unrendered')
            # Forcer le rechargement de la page
            st.rerun()
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du bouton de déconnexion: {format_exception(e)}")
        st.error(f"Erreur lors de l'affichage du bouton de déconnexion: {str(e)}")

def show_error_page(error_message="Une erreur s'est produite"):
    """Affiche une page d'erreur.
    
    Args:
        error_message: Message d'erreur à afficher
    """
    st.markdown("<h1 style='text-align: center;'>Assistant de Recherche M&A</h1>", unsafe_allow_html=True)
    st.warning(f"{error_message}. Veuillez réessayer plus tard ou contacter l'administrateur.")
