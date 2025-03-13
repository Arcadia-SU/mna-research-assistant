import os
import yaml
import streamlit as st
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from utils.logger import setup_logger
from utils.exception_utils import format_exception

# Configuration du logging
logger = setup_logger("auth_service")

class AuthService:
    """Service de gestion de l'authentification."""
    
    def __init__(self, credentials_path="config/credentials.yaml"):
        """Initialise le service d'authentification."""
        self.credentials_path = credentials_path
        self.config = None
        self.authenticator = None
        
        # Essayer d'abord de charger depuis les secrets Streamlit si disponibles
        if hasattr(st, 'secrets') and 'auth_config' in st.secrets:
            logger.info("Utilisation de la configuration depuis les secrets Streamlit")
            self.config = st.secrets['auth_config']
        else:
            # Sinon, charger depuis le fichier
            self.load_config()
            
        self.initialize_authenticator()
    
    def load_config(self):
        """Charge la configuration depuis le fichier YAML."""
        try:
            # D'abord essayer de charger le fichier credentials.yaml (fichier réel)
            if not os.path.exists(self.credentials_path):
                self.credentials_path = "config/example_credentials.yaml"
                logger.warning("Utilisation du fichier d'authentification d'exemple.")
            
            logger.info(f"Chargement du fichier de configuration: {self.credentials_path}")
            with open(self.credentials_path, 'r') as file:
                self.config = yaml.load(file, Loader=SafeLoader)
            
            # Afficher des informations détaillées sur la configuration
            # self.debug_config()
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {format_exception(e)}")
            raise e
    
    def initialize_authenticator(self):
        """Initialise l'objet authentificateur."""
        try:
            logger.info("Création de l'objet Authenticate")
            self.authenticator = stauth.Authenticate(
                self.config['credentials'],
                self.config['cookie']['name'],
                self.config['cookie']['key'],
                self.config['cookie']['expiry_days'],
                self.config.get('preauthorized', {}).get('emails', [])
            )
            logger.info("Objet Authenticate créé avec succès")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'authentificateur: {format_exception(e)}")
            raise e
    
    def login(self, location='main'):
        """Gère la tentative de connexion de l'utilisateur."""
        try:
            logger.debug("Appel de la méthode login() de l'authentificateur")
            
            self.authenticator.login(
                location=location,
                fields={
                    'Form name': 'Connexion', 
                    'Username': 'Identifiant', 
                    'Password': 'Mot de passe', 
                    'Login': 'Se connecter'
                }
            )
            
            # Récupérer les valeurs depuis st.session_state
            name = st.session_state.get("name", None)
            authentication_status = st.session_state.get("authentication_status", None)
            username = st.session_state.get("username", None)
            
            logger.info(f"État de la session après login: name={name}, auth_status={authentication_status}, username={username}")
            
            return authentication_status, name, username
        
        except Exception as e:
            logger.error(f"Erreur pendant la connexion: {format_exception(e)}")
            raise e
    
    def logout(self, location='main', button_name="Déconnexion"):
        """Gère la déconnexion de l'utilisateur."""
        try:
            logger.debug("Ajout du bouton de déconnexion")
            self.authenticator.logout(location=location, button_name=button_name)
            logger.debug("Bouton de déconnexion ajouté avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du bouton de déconnexion: {format_exception(e)}")
            raise e
    
    def get_username_list(self):
        """Retourne la liste des noms d'utilisateurs disponibles."""
        if self.config and 'credentials' in self.config and 'usernames' in self.config['credentials']:
            return list(self.config['credentials']['usernames'].keys())
        return []
    
    def debug_config(self):
        """Affiche les détails de la configuration pour debug."""
        logger.debug(f"--- DEBUG CONFIG ---")
        logger.debug(f"Cookie: {self.config.get('cookie', {})}")
        
        credentials = self.config.get('credentials', {})
        logger.debug(f"Credentials structure: {list(credentials.keys())}")
        
        usernames = credentials.get('usernames', {})
        logger.debug(f"Usernames: {list(usernames.keys())}")
        
        for username, data in usernames.items():
            logger.debug(f"Username: {username}")
            # Ne pas logger les mots de passe en clair
            password_info = "Set" if data.get('password') else "Not set"
            logger.debug(f"  - Email: {data.get('email')}")
            logger.debug(f"  - Password: {password_info}")
            logger.debug(f"  - Roles: {data.get('roles', [])}")
            logger.debug(f"  - Failed attempts: {data.get('failed_login_attempts', 0)}")
            logger.debug(f"  - Logged in: {data.get('logged_in', False)}")
        
        logger.debug(f"Preauthorized: {self.config.get('preauthorized', {})}")
        logger.debug(f"--- END DEBUG CONFIG ---")
