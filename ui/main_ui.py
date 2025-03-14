import streamlit as st
from PIL import Image
from services.llm_service import LLMService
from utils.logger import setup_logger
from streamlit_extras.stylable_container import stylable_container

# Configuration du logging
logger = setup_logger("main_ui")

def main_app_ui():
    """Interface utilisateur principale de l'application après authentification."""
    # Appliquer les styles CSS depuis styles.py
    from ui.styles import apply_chat_styles
    apply_chat_styles()

    # Charger l'image pour l'avatar
    try:
        assistant_avatar = Image.open('assets/logo-scalene.webp')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'image: {e}")
        assistant_avatar = ""  # Utiliser un placeholder en cas d'erreur

    # Utiliser une icône Material Design pour l'avatar utilisateur (équivalent à person-circle de Bootstrap)
    user_avatar = "assets/person-circle.svg"

    # Initialiser l'historique du chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "Vous êtes un assistant de recherche en fusions-acquisitions. Votre objectif est d'aider les analystes à effectuer des recherches pertinentes sur des transactions et des entreprises."}
        ]

    # Initialiser le service LLM
    llm = LLMService()

    # Initialiser le state pour le input
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    # Fonction de callback pour traiter l'envoi
    def process_input():
        # Stocker la valeur actuelle
        prompt = st.session_state.chat_input
        # Vider immédiatement l'entrée
        st.session_state.chat_input = ""
        
        if prompt:
            # Traiter le message
            st.session_state.user_input = prompt
    
    # Titre centré avec style minimaliste
    st.markdown("<div class='title-container'><h1 class='app-title'> Assistant de Recherche M&A</h1></div>", unsafe_allow_html=True)
    
    # Créer un container pour les messages du chat
    message_container = st.container()
    
    # Champ de saisie déjà stylisé par le CSS personnalisé
    prompt = st.text_input("Posez votre question sur les transactions M&A:", key="chat_input", on_change=process_input)
    
    # Afficher tous les messages (historique et nouveaux) dans le message_container
    with message_container:
        # Afficher l'historique des messages (sauf le message système)
        for message in st.session_state.messages[1:]:  # Ignorer le message système
            if message["role"] == "user":
                with st.chat_message(message["role"], avatar=user_avatar):
                    st.markdown(message["content"])
            else:
                with st.chat_message(message["role"], avatar=assistant_avatar):
                    st.markdown(message["content"])

    # Traiter l'entrée utilisateur stockée dans session_state
    if st.session_state.user_input:
        prompt = st.session_state.user_input
        st.session_state.user_input = ""  # Réinitialiser pour le prochain tour
        
        # Ajouter la requête à l'historique
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Ajouter la requête à la conversation envoyée à l'API
        messages_for_api = st.session_state.messages.copy()
        
        # Afficher le message utilisateur et la réponse (pas besoin car ils seront affichés au prochain rechargement)
        with message_container:
            with st.chat_message("user", avatar=user_avatar):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar=assistant_avatar), st.empty(): # (Bug de streamlit : texte fantôme dupliqué si on n'ajoute pas cet empty)
                stream = llm.get_stream(st.session_state.messages)
                response = st.write_stream(stream)
        
        # Ajouter la réponse à l'historique
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Créer une ligne avec deux colonnes pour les boutons
    if len(st.session_state.messages) > 2:  # Plus que le message système + 1 échange
        col1, col2 = st.columns([3, 1])
        
        # Bouton Nouvelle conversation dans la première colonne (plus large)
        with col1:
            if st.button("Nouvelle conversation"):
                st.session_state.messages = [st.session_state.messages[0]]  # Garder uniquement le message système
                st.experimental_rerun()
        
        # Bouton de déconnexion dans la deuxième colonne (plus étroite) avec alignement à droite
        with col2:
            # Utiliser stylable_container pour aligner le bouton à droite
            with stylable_container(
                key="logout_button_container",
                css_styles="""
                    {
                        display: flex;
                        justify-content: flex-end;
                    }
                    button {
                        margin: 0;
                    }
                """
            ):
                if st.button("", icon=":material/logout:", help="Se déconnecter", type="tertiary", key="logout_button"):
                    # Réinitialiser toutes les variables de session
                    for key in list(st.session_state.keys()):
                        if key != "_is_running" and key != "_script_run_ctx":
                            try:
                                del st.session_state[key]
                            except:
                                pass
                    st.rerun()
