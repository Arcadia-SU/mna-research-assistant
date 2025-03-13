import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from yaml.dumper import SafeDumper
import os

def generate_hashed_passwords():
    """
    Génère des hash pour les mots de passe en clair dans le fichier credentials.yaml
    Sauvegarde le fichier mis à jour avec les mots de passe hachés
    """
    config_file = "config/credentials.yaml"
    
    # Vérifier si le fichier existe
    if not os.path.exists(config_file):
        print(f"Le fichier {config_file} n'existe pas.")
        return
    
    # Charger la configuration
    with open(config_file, 'r') as file:
        config = yaml.load(file, SafeLoader)
    
    # Vérifier s'il y a des utilisateurs
    if not config.get('credentials', {}).get('usernames', {}):
        print("Aucun utilisateur trouvé dans le fichier de configuration.")
        return
    
    # Hacher les mots de passe
    hashed_passwords = {}
    updated = False
    
    for username, user_data in config['credentials']['usernames'].items():
        password = user_data.get('password')
        # Vérifier si le mot de passe est déjà haché
        if password and not password.startswith('$2b$'):
            # Dans la version ≥0.4.2, Hasher ne prend pas de liste en paramètre
            hasher = stauth.Hasher()
            hashed_passwords[username] = hasher.hash(password)
            updated = True
        else:
            hashed_passwords[username] = password
    
    # Mettre à jour les mots de passe dans la configuration
    if updated:
        for username, hashed_password in hashed_passwords.items():
            config['credentials']['usernames'][username]['password'] = hashed_password
        
        # Sauvegarder la configuration mise à jour
        with open(config_file, 'w') as file:
            yaml.dump(config, file, Dumper=SafeDumper)
        
        print("Les mots de passe ont été hachés et le fichier a été mis à jour.")
    else:
        print("Tous les mots de passe sont déjà hachés ou aucun mot de passe à hacher n'a été trouvé.")

if __name__ == "__main__":
    generate_hashed_passwords()