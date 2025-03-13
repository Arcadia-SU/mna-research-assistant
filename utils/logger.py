import logging

def setup_logger(name="mna_app"):
    """Configure et retourne un logger pour l'application."""
    logger = logging.getLogger(name)
    
    # Configurer le logger seulement s'il n'y a pas de gestionnaires
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Formater
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # On pourrait ajouter un handler pour un fichier de log ici
        
    return logger
