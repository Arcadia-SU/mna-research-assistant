import traceback

def format_exception(e):
    """Formate une exception pour l'affichage et le logging."""
    return f"Exception: {str(e)}\n\nStacktrace:\n{''.join(traceback.format_tb(e.__traceback__))}"
