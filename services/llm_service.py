import time
import streamlit as st
from openai import OpenAI
from openai.types.beta.threads import Run
from openai.types.beta.threads.runs import RunStep

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        self.assistant_id = st.secrets.get("OPENAI_ASSISTANT_ID", "votre_assistant_id_par_défaut")
    
    def get_stream(self, messages: list) -> dict:
        """
        Crée un stream de réponses depuis l'API OpenAI Assistants avec statut.
        """
        # Créer ou récupérer un thread existant
        if "thread_id" not in st.session_state:
            thread = self.client.beta.threads.create()
            st.session_state.thread_id = thread.id
        
        thread_id = st.session_state.thread_id
        
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
        
        # Utiliser create_and_stream pour le streaming
        with self.client.beta.threads.runs.create_and_stream(**run_params) as stream:
            message_being_created = ""
            
            for event in stream:
                # Afficher le statut actuel
                if event.event == "thread.run.created":
                    status_placeholder.info("Démarrage de l'analyse...")
                
                elif event.event == "thread.run.queued":
                    status_placeholder.info("En file d'attente...")
                
                elif event.event == "thread.run.in_progress":
                    status_placeholder.info("Analyse en cours...")
                
                # Pour les étapes du run (tool calls, etc.)
                elif event.event == "thread.run.step.created" or event.event == "thread.run.step.in_progress":
                    # Récupérer des détails sur l'étape
                    if hasattr(event, 'data') and hasattr(event.data, 'step_details'):
                        step_type = getattr(event.data.step_details, 'type', 'action')
                        if step_type == "message_creation":
                            status_placeholder.info(f"En pleine réflexion...")   
                        elif step_type == "tool_calls":
                            status_placeholder.info(f"Se met au travail...")
                        else:
                            status_placeholder.info(f"Exécution de: {step_type}...")
                
                # Pour le streaming du message
                elif event.event == "thread.message.delta":
                    if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'content'):
                        for content_delta in event.data.delta.content:
                            if content_delta.type == 'text' and hasattr(content_delta.text, 'value'):
                                chunk = content_delta.text.value
                                message_being_created += chunk
                                # Masquer le statut une fois que le texte commence à arriver
                                status_placeholder.empty()
                                yield chunk
                
                elif event.event == "thread.run.completed":
                    status_placeholder.empty()
                    break
                
                elif event.event == "thread.run.failed":
                    error_message = "Erreur dans le traitement"
                    if hasattr(event.data, 'last_error'):
                        error_message = f"Erreur: {event.data.last_error.message}"
                    status_placeholder.error(error_message)
                    yield f"\n\n{error_message}"
                    break
        
        # Fallback en cas d'absence de streaming
        if not message_being_created:
            status_placeholder.empty()
            messages_response = self.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            if messages_response.data:
                assistant_messages = [m for m in messages_response.data if m.role == "assistant"]
                if assistant_messages:
                    latest_message = assistant_messages[0]
                    for content_block in latest_message.content:
                        if content_block.type == "text":
                            yield content_block.text.value
    
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
                
                streamlit_messages.append({"role": role, "content": content})
            
            return streamlit_messages
        except Exception as e:
            st.error(f"Erreur lors de la récupération de l'historique: {e}")
            # En cas d'erreur, renvoyer au moins le message système
            return [{"role": "system", "content": "Tu es un assistant de recherche spécialisé en M&A, qui va faire une recherche pour l'utilisateur..."}]