import json
import os
import time
import random
import streamlit as st
from openai import OpenAI
from openai.types.beta.threads import Run
from openai.types.beta.threads.runs import RunStep

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        self.assistant_id = st.secrets.get("OPENAI_ASSISTANT_ID", "votre_assistant_id_par_défaut")
        # Dictionnaire pour stocker les fichiers par ID de message
        if "message_files" not in st.session_state:
            st.session_state.message_files = {}
    
    def get_stream(self, messages: list) -> dict:
        """
        Crée un stream de réponses depuis l'API OpenAI Assistants avec statut.
        """
        # Import ici pour éviter les dépendances circulaires
        from services.api_tools import APITools
        
        # Initialiser les outils API
        api_tools = APITools()
        
        # Créer ou récupérer un thread existant
        if "thread_id" not in st.session_state:
            thread = self.client.beta.threads.create()
            st.session_state.thread_id = thread.id
        
        thread_id = st.session_state.thread_id
        
        # Vérifier si un run est déjà actif sur ce thread
        active_runs = self.client.beta.threads.runs.list(thread_id=thread_id, limit=5)
        
        # Attendre que tous les runs actifs soient terminés avant de continuer
        for run in active_runs.data:
            if run.status in ["queued", "in_progress", "requires_action"]:
                # Si le run est toujours actif après les tentatives, avertir l'utilisateur
                yield "⚠️ Une autre tâche est encore en cours de traitement. Veuillez attendre qu'elle soit terminée avant d'envoyer un nouveau message."
                return
        
        # Ajouter le dernier message utilisateur au thread
        user_messages = [m for m in messages if m["role"] == "user"]
        if user_messages:
            last_user_message = user_messages[-1]
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=last_user_message["content"]
            )
        
        # Récupérer les instructions système s'il y en a
        system_message = next((m["content"] for m in messages if m["role"] == "system"), None)
        
        # Paramètres du run
        run_params = {
            "assistant_id": self.assistant_id,
            "thread_id": thread_id,
        }
        
        # Créer et démarrer un statut
        status_placeholder = st.empty()
        
        # ID du message courant (à initialiser plus tard)
        current_message_id = None
        
        # Utiliser stream pour le streaming
        with self.client.beta.threads.runs.stream(**run_params) as stream:
            message_being_created = ""
            run_id = None
            
            for event in stream:
                # Sauvegarder le run_id dès qu'il est disponible
                if event.event == "thread.run.created" and hasattr(event, 'data'):
                    run_id = event.data.id
                    status_placeholder.info(random.choice([
                        "Hop, je note...",
                        "Hm ?",
                    ]))
                
                elif event.event == "thread.run.queued":
                    status_placeholder.info(random.choice([
                        "Petite préparation...",
                        "Ça vient...",
                        "Faisons un peu de place...",
                        "Je m'installe..."
                    ]))
                
                elif event.event == "thread.run.in_progress":
                    status_placeholder.info(random.choice([
                        "Hm...",
                        "C'est parti...",
                        "Je m'y met..."
                    ]))
                
                # Pour les étapes du run (tool calls, etc.)
                elif event.event == "thread.run.step.created" or event.event == "thread.run.step.in_progress":
                    # Récupérer des détails sur l'étape
                    if hasattr(event, 'data') and hasattr(event.data, 'step_details'):
                        step_type = getattr(event.data.step_details, 'type', 'action')
                        if step_type == "message_creation":
                            status_placeholder.info(f"Voyons voir...")   
                        elif step_type == "tool_calls":
                            status_placeholder.info(f"*Prépare la requête...*")
                
                # Gestion des tool calls (function calls)
                elif event.event == "thread.run.requires_action":
                    if hasattr(event.data, 'required_action') and hasattr(event.data.required_action, 'submit_tool_outputs'):
                        tool_calls = event.data.required_action.submit_tool_outputs.tool_calls
                        tool_outputs = []
                        
                        # Traiter chaque outil appelé
                        for tool_call in tool_calls:
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            
                            status_placeholder.info("Recherche d'entreprises..." if function_name == "get_company_targets" else "Recherche de transactions...")
                            
                            # Diriger vers l'API ArcadiaAgents
                            result = None
                            api_result = None
                            
                            try:
                                # Préparation du payload pour l'API ArcadiaAgents
                                # Utiliser directement l'event_type et les données telles quelles
                                payload = function_args    
                                
                                # Afficher les arguments de l'appel d'outil
                                print(f"\nAppel de la fonction: {function_name}")
                                print(f"Arguments: {json.dumps(function_args, indent=2)}")

                                # Appel à l'API via APITools
                                api_result = api_tools.call_async_api(payload)
                                                                 
                                # Vérifier si l'appel a réussi
                                if api_result.get("success", False):
                                    # Récupérer et stocker temporairement les fichiers générés si présents
                                    downloaded_files = api_result.get("downloaded_files", [])
                                    
                                    # Nous allons stocker temporairement les fichiers pour les associer au prochain message
                                    # de l'assistant plutôt qu'au message courant
                                    if "pending_files" not in st.session_state:
                                        st.session_state.pending_files = []
                                    
                                    # Stocker les fichiers en attente d'association avec le prochain message
                                    for file_data in downloaded_files:
                                        st.session_state.pending_files.append({
                                            "filename": file_data.get("filename", "file"),
                                            "type": file_data.get("type", "unknown"),
                                            "content": file_data.get("content")
                                        })
                                    
                                    # Informer l'utilisateur
                                    if downloaded_files:
                                        status_placeholder.success(f"{len(downloaded_files)} fichier(s) de résultats récupéré(s)")
                                    
                                    # Construire le résultat pour OpenAI
                                    result = {
                                        "success": True,
                                        "message": "Traitement terminé avec succès",
                                        "event_data": api_result.get("event_data", {}),
                                        "files_info": [
                                            {"filename": f.get("filename"), "type": f.get("type")} 
                                            for f in downloaded_files
                                        ]
                                    }
                                else:
                                    # Gestion de l'erreur
                                    error_msg = api_result.get("error", "Erreur inconnue")
                                    
                                    # Détection spécifique de l'erreur de délai dépassé
                                    if error_msg == "Délai d'attente dépassé":
                                        yield f"⚠️ Le temps d'attente maximal a été dépassé pour cette requête. Il y a sûrement eu une erreur. Veuillez réessayer."
                                        # Continuer sans ajouter ce résultat aux tool_outputs pour éviter un nouvel appel
                                        continue
                                        
                                    status_placeholder.error(f"Erreur: {error_msg}")
                                    result = {
                                        "success": False,
                                        "message": f"Erreur lors du traitement: {error_msg}"
                                    }
                            except Exception as e:
                                # Gestion des exceptions
                                status_placeholder.error(f"Exception: {str(e)}")
                                result = {
                                    "success": False,
                                    "message": f"Erreur lors du traitement: {str(e)}"
                                }
                            
                            # Ajouter le résultat au format attendu par submit_tool_outputs
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(result)
                            })
                        
                        # Soumettre tous les résultats à OpenAI pour indiquer que les appels d'outils sont terminés
                        # Utiliser submit_tool_outputs_stream avec l'API basée sur les événements
                        status_placeholder.info("Récupération de la réponse...")
                        
                        # Au lieu d'attendre la fin avec until_done, utiliser un gestionnaire d'événements
                        # pour traiter le stream en temps réel
                        with self.client.beta.threads.runs.submit_tool_outputs_stream(
                            thread_id=thread_id,
                            run_id=run_id,
                            tool_outputs=tool_outputs
                        ) as stream:
                            for event in stream:
                                # Traiter les événements de delta de message pour le streaming en temps réel
                                if event.event == "thread.message.delta":
                                    if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'content'):
                                        # Récupérer l'ID du message si disponible et pas encore défini
                                        if current_message_id is None and hasattr(event.data, 'message_id'):
                                            current_message_id = event.data.message_id
                                            # Initialiser un conteneur pour les fichiers de ce message
                                            if current_message_id not in st.session_state.message_files:
                                                st.session_state.message_files[current_message_id] = []
                                                
                                        for content_delta in event.data.delta.content:
                                            if content_delta.type == 'text' and hasattr(content_delta.text, 'value'):
                                                chunk = content_delta.text.value
                                                message_being_created += chunk
                                                # Masquer le statut une fois que le texte commence à arriver
                                                status_placeholder.empty()
                                                yield chunk
                                
                                # Quand un message est créé, on enregistre son ID pour associer les fichiers
                                elif event.event == "thread.message.created":
                                    message_data = event.data
                                    message_id = message_data.id
                                    
                                    # Initialiser la liste des fichiers pour ce message si nécessaire
                                    if message_id not in st.session_state.message_files:
                                        st.session_state.message_files[message_id] = []
                                        
                                    # Noter l'ID du message courant pour associer les fichiers
                                    current_message_id = message_id
                                    
                                    # Si nous avons des fichiers en attente, les associer à ce nouveau message
                                    if "pending_files" in st.session_state and st.session_state.pending_files:
                                        print(f"Association de {len(st.session_state.pending_files)} fichiers en attente avec le message {message_id}")
                                        # Transférer les fichiers en attente vers ce message
                                        st.session_state.message_files[message_id].extend(st.session_state.pending_files)
                                        # Vider la liste des fichiers en attente
                                        st.session_state.pending_files = []
                                
                                elif event.event == "thread.run.completed":
                                    # Si le message a été complètement streamé, continuer
                                    if message_being_created:
                                        status_placeholder.empty()
                                        continue
                                    
                                    # Si on n'a pas encore reçu de message streamé, récupérer explicitement
                                    # le dernier message (cas où le streaming n'a pas fonctionné)
                                    if current_message_id:
                                        # Afficher les fichiers associés au message à la fin
                                        if current_message_id in st.session_state.message_files and st.session_state.message_files[current_message_id]:
                                            print(f"Fichiers à afficher pour le message {current_message_id}: {len(st.session_state.message_files[current_message_id])}")
                                            # Ne pas afficher les fichiers ici, ils seront affichés une seule fois à la fi
                                
                                elif event.event == "thread.run.failed":
                                    error_message = "Erreur dans le traitement"
                                    if hasattr(event.data, 'last_error'):
                                        error_message = f"Erreur: {event.data.last_error.message}"
                                    status_placeholder.error(error_message)
                                    yield f"\n\n{error_message}"
                                    break
                        
                # Pour le streaming du message
                elif event.event == "thread.message.delta":
                    if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'content'):
                        # Récupérer l'ID du message si disponible et pas encore défini
                        if current_message_id is None and hasattr(event.data, 'message_id'):
                            current_message_id = event.data.message_id
                            # Initialiser un conteneur pour les fichiers de ce message
                            if current_message_id not in st.session_state.message_files:
                                st.session_state.message_files[current_message_id] = []
                                
                        for content_delta in event.data.delta.content:
                            if content_delta.type == 'text' and hasattr(content_delta.text, 'value'):
                                chunk = content_delta.text.value
                                message_being_created += chunk
                                # Masquer le statut une fois que le texte commence à arriver
                                status_placeholder.empty()
                                yield chunk
                
                elif event.event == "thread.run.completed":
                    status_placeholder.empty()
                    # Forcer l'affichage des fichiers à la fin du streaming si possible
                    if current_message_id and current_message_id in st.session_state.message_files:
                        self.display_message_files(current_message_id)
                    break
                
                elif event.event == "thread.run.failed":
                    error_message = "Erreur dans le traitement"
                    if hasattr(event.data, 'last_error'):
                        error_message = f"Erreur: {event.data.last_error.message}"
                    status_placeholder.error(error_message)
                    yield f"\n\n{error_message}"
                    break
    
    def get_run_steps(self, thread_id, run_id):
        """
        Récupère les étapes détaillées d'un run pour affichage
        """
        try:
            steps = self.client.beta.threads.runs.steps.list(
                thread_id=thread_id,
                run_id=run_id,
                limit=10
            )
            return steps.data
        except Exception as e:
            st.error(f"Erreur lors de la récupération des étapes: {e}")
            return []

    def get_thread_messages(self):
        """
        Récupère l'historique complet des messages depuis l'API OpenAI Assistants.
        Retourne une liste au format compatible avec l'affichage Streamlit.
        """
        # Vérifier si un thread existe
        if "thread_id" not in st.session_state:
            # Pas d'historique disponible
            return [{"role": "system", "content": "Tu es un assistant de recherche spécialisé en M&A, qui va faire une recherche pour l'utilisateur..."}]
        
        thread_id = st.session_state.thread_id
        
        try:
            # Récupérer tous les messages du thread
            messages_response = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="asc"  # Du plus ancien au plus récent
            )
            
            # Convertir au format attendu par Streamlit
            streamlit_messages = [{"role": "system", "content": "Tu es un assistant de recherche spécialisé en M&A, qui va faire une recherche pour l'utilisateur..."}]
            
            for message in messages_response.data:
                role = "user" if message.role == "user" else "assistant"
                content = ""
                
                # Extraire le contenu textuel
                for content_block in message.content:
                    if content_block.type == "text":
                        content += content_block.text.value
                
                # Ajouter l'ID du message pour pouvoir l'associer à des fichiers
                streamlit_message = {
                    "role": role, 
                    "content": content,
                    "message_id": message.id
                }
                
                streamlit_messages.append(streamlit_message)
            
            return streamlit_messages
        except Exception as e:
            st.error(f"Erreur lors de la récupération de l'historique: {e}")
            # En cas d'erreur, renvoyer au moins le message système
            return [{"role": "system", "content": "Tu es un assistant de recherche spécialisé en M&A, qui va faire une recherche pour l'utilisateur..."}]

    def _display_file(self, file_name, file_type, file_content):
        # Cette méthode ne sera plus appelée directement, mais depuis le fichier principal
        # qui affiche les messages, pour chaque message spécifique
        if file_type == "image":
            st.image(file_content)
        elif file_type == "csv":
            try:
                # Utiliser pandas pour lire et afficher le CSV
                import pandas as pd
                import io
                
                # Créer un DataFrame à partir du contenu binaire
                df = pd.read_csv(io.BytesIO(file_content))
                
                # Ajouter un espace pour séparer le message des données
                st.write("")
                
                # Afficher le DataFrame dans un expander comme le mockup
                with st.expander("Résultats de l'analyse", expanded=True):
                    st.dataframe(df, use_container_width=True)
                    
                    # Proposer un téléchargement
                    st.download_button(
                        label="Télécharger les résultats (CSV)",
                        data=file_content,
                        file_name=file_name,
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"Erreur lors de l'affichage du CSV: {str(e)}")
        elif file_type == "excel":
            try:
                # Utiliser pandas pour lire et afficher l'Excel
                import pandas as pd
                import io
                
                # Créer un DataFrame à partir du contenu binaire
                df = pd.read_excel(io.BytesIO(file_content))
                
                # Afficher le DataFrame
                st.dataframe(df)
                
                # Proposer un téléchargement
                st.download_button(
                    label=f"Télécharger {file_name}",
                    data=file_content,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Erreur lors de l'affichage de l'Excel: {str(e)}")
        elif file_type == "text":
            st.write(file_content)
        elif file_type == "pdf":
            with open(file_name, "wb") as f:
                f.write(file_content)
            st.download_button("Télécharger le fichier", file_content, file_name, mime="application/pdf")
        else:
            # Pour les types non reconnus, proposer un téléchargement générique
            st.write(f"Type de fichier: {file_type}")
            st.download_button(
                label=f"Télécharger {file_name}",
                data=file_content,
                file_name=file_name
            )
    
    def display_message_files(self, message_id):
        """
        Affiche les fichiers associés à un message spécifique.
        
        Args:
            message_id (str): L'ID du message pour lequel afficher les fichiers
        """
        if "message_files" not in st.session_state or message_id not in st.session_state.message_files:
            return
            
        for file_data in st.session_state.message_files[message_id]:
            self._display_file(
                file_data["filename"],
                file_data["type"],
                file_data["content"]
            )