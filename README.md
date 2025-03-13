# M&A Research Assistant

Un assistant de recherche intelligent pour les professionnels de la finance spécialisés dans les fusions et acquisitions (M&A). Cette application utilise l'API OpenAI Assistants pour fournir des réponses précises et contextuelles aux questions sur les valorisations M&A et autres sujets financiers.

## Fonctionnalités

- Interface utilisateur minimaliste et moderne
- Authentification sécurisée pour restreindre l'accès
- Conversations IA fluides avec streaming des réponses
- Mémorisation du contexte des conversations
- Design réactif et animations subtiles

## Installation

1. Clonez ce dépôt:
   ```bash
   git clone https://github.com/votre-username/mna-research-assistant.git
   cd mna-research-assistant
   ```

2. Installez les dépendances:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurez vos secrets:
   - Créez un fichier `.streamlit/secrets.toml` basé sur `.streamlit/secrets.example.toml`
   - Ajoutez votre clé API OpenAI et ID d'assistant
   - Configurez vos informations d'authentification

4. Pour utiliser l'authentification avec streamlit-authenticator:
   - Créez un fichier `config/credentials.yml` basé sur `config/example_credentials.yaml`
   - Ajustez les utilisateurs et mots de passe selon vos besoins

## Utilisation

Lancez l'application localement:
```bash
streamlit run app.py
```

## Déploiement

Pour déployer sur Streamlit Cloud:
1. Poussez ce dépôt sur GitHub
2. Connectez-vous à [Streamlit Cloud](https://streamlit.io/cloud)
3. Déployez l'application depuis votre dépôt GitHub
4. Ajoutez vos secrets dans l'interface Streamlit Cloud

## Structure du projet

```
mna-research-assistant/
├── .streamlit/             # Configuration Streamlit
├── app.py                  # Application principale
├── assets/                 # Images et ressources
├── config/                 # Fichiers de configuration
├── requirements.txt        # Dépendances
└── services/               # Services et modules
    └── llm_service.py      # Service d'intégration OpenAI
```

## Licence

Ce projet est sous licence [MIT](LICENSE).
