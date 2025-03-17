import time
import requests
import streamlit as st
import pandas as pd
import json

class APITools:
    def __init__(self, base_url="https://api.arcadia-agents.com"):
        self.base_url = base_url
        # Vous pouvez ajouter des headers d'authentification si nécessaire
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {st.secrets.get('API_KEY', '')}"
        }
    
    def submit_event(self, payload):
        """
        Soumet un événement à l'API et retourne l'event_id.
        
        Args:
            payload (dict): Le payload JSON à envoyer à l'API
            
        Returns:
            dict: Contient l'event_id et le message de confirmation, ou une erreur
        """
        try:
            print("Envoi d'une requête à l'endpoint /events : création d'un nouvel évènement")
            response = requests.post(
                f"{self.base_url}/events", 
                json=payload, 
                headers=self.headers
            )
            
            if response.status_code == 202:  # Accepted
                response_data = response.json()
                return {
                    "success": True,
                    "event_id": response_data.get("event_id"),
                    "message": response_data.get("message")
                }
            elif response.status_code == 422:  # Unprocessable Entity
                print(f"DEBUG - Erreur 422 : {response.text}")
                return {
                    "success": False,
                    "error": f"Erreur lors de la soumission: {response.status_code}",
                    "details": response.text
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur lors de la soumission: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            print(f"DEBUG - Exception lors de la soumission: {str(e)}")
            return {
                "success": False,
                "error": f"Exception lors de la soumission: {str(e)}"
            }
    
    def check_event_status(self, event_id):
        """
        Vérifie l'état d'un événement.
        
        Args:
            event_id (str): L'ID de l'événement à vérifier
            
        Returns:
            dict: Les détails de l'événement ou une erreur
        """
        try:
            print("Envoi d'une requête à l'endpoint /events/{event_id} : vérification d'un évènement existant")
            response = requests.get(
                f"{self.base_url}/events/{event_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur lors de la vérification: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception lors de la vérification: {str(e)}"
            }
    
    def download_file(self, file_id):
        """
        Télécharge un fichier depuis l'API.
        
        Args:
            file_id (str): L'ID du fichier à télécharger
            
        Returns:
            dict: Contient le contenu du fichier ou une erreur
        """
        try:
            print("Envoi d'une requête à l'endpoint /files/{file_id} : téléchargement d'un fichier existant")
            response = requests.get(
                f"{self.base_url}/files/{file_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "content": response.content,
                    "content_type": response.headers.get("Content-Type")
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur lors du téléchargement: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception lors du téléchargement: {str(e)}"
            }
    
    def call_async_api(self, payload, display_status=True):
        """
        Appelle l'API ArcadiaAgents de manière asynchrone et suit le processus jusqu'à la complétion.
        
        Args:
            payload (dict): Le payload JSON à envoyer pour l'événement
            display_status (bool): Afficher le statut dans l'interface Streamlit
            
        Returns:
            dict: Résultat final avec les données et/ou fichiers
        """
        # Afficher un placeholder pour les mises à jour de statut
        if display_status:
            status_placeholder = st.empty()
            status_placeholder.info("Soumission de la tâche en cours...")
        
        # 1. Soumettre l'événement
        submit_result = self.submit_event(payload)
        
        if not submit_result.get("success"):
            error_msg = submit_result.get('error', 'Erreur inconnue')
            details = submit_result.get('details', 'Pas de détails disponibles')
            print(f"DEBUG - Échec de la soumission: {error_msg}")
            print(f"DEBUG - Détails de l'erreur: {details}")
            
            if display_status:
                status_placeholder.error(f"Erreur: {error_msg}")
                
            # Créer une réponse d'erreur formatée pour l'assistant
            error_response = {
                "success": False,
                "error": error_msg,
                "details": details,
                "message": "L'API a rencontré une erreur de validation. Veuillez vérifier les paramètres soumis."
            }
            
            return error_response
        
        event_id = submit_result.get("event_id")
        
        if display_status:
            status_placeholder.info(f"Tâche soumise (ID: {event_id}). Traitement en cours...")
        
        # 2. Suivre l'état jusqu'à la complétion
        max_attempts = 60  # 2 minutes maximum (avec 2s entre chaque tentative)
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(2)  # Attendre 2 secondes entre les vérifications
            attempt += 1
            
            if display_status:
                status_placeholder.info(f"Vérification de l'état... ({attempt}/{max_attempts})")
            
            status_result = self.check_event_status(event_id)
            
            if not status_result.get("success"):
                if display_status:
                    status_placeholder.warning(f"Erreur lors de la vérification: {status_result.get('error')}")
                continue
            
            event_data = status_result.get("data", {})
            event_status = event_data.get("status")
            
            if event_status == "completed":
                if display_status:
                    status_placeholder.success("Traitement terminé !")
                
                # 3. Récupérer les fichiers si présents
                files = event_data.get("files", [])
                downloaded_files = []
                
                if files and len(files) > 0:
                    if display_status:
                        status_placeholder.info(f"Téléchargement de {len(files)} fichier(s)...")
                    
                    for file_info in files:
                        file_id = file_info.get("id")
                        file_name = file_info.get("filename", "unknown")
                        file_type = file_info.get("type", "unknown")
                        
                        file_result = self.download_file(file_id)
                        
                        if file_result.get("success"):
                            downloaded_files.append({
                                "file_id": file_id,
                                "filename": file_name,
                                "type": file_type,
                                "content": file_result.get("content"),
                                "content_type": file_result.get("content_type")
                            })
                        else:
                            if display_status:
                                status_placeholder.warning(f"Échec du téléchargement du fichier {file_name}: {file_result.get('error')}")
                
                # 4. Nettoyer le placeholder et retourner les résultats
                if display_status:
                    status_placeholder.empty()
                
                return {
                    "success": True,
                    "event_data": event_data,
                    "downloaded_files": downloaded_files
                }
            
            elif event_status == "processing":
                if display_status:
                    # Mettre à jour le statut avec les détails disponibles
                    task_context = event_data.get("task_context", {})
                    nodes = task_context.get("nodes", [])
                    
                    if nodes and len(nodes) > 0:
                        last_node = nodes[-1]
                        status_message = f"En cours: {last_node.get('name', 'Traitement')} - {last_node.get('status', 'en cours')}"
                        status_placeholder.info(status_message)
                    else:
                        status_placeholder.info(f"Traitement en cours... ({attempt*2}/{max_attempts*2}s)")
            else:
                if display_status:
                    status_placeholder.warning(f"État inattendu: {event_status}")
        
        # Délai dépassé
        if display_status:
            status_placeholder.error("Délai d'attente dépassé pour la tâche")
        
        return {
            "success": False,
            "error": "Délai d'attente dépassé",
            "event_id": event_id
        }