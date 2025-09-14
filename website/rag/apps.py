from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class RagConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag'
    verbose_name = 'RAG System'

    def ready(self):
        """
        Initialize RAG systems when Django starts.
        This method is called when the Django application is ready.
        """
        # Only initialize in the main process, not in subprocesses
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        try:
            # Import here to avoid circular imports
            from .rag_manager import rag_manager
            
            # Initialize RAG systems
            logger.info("🚀 Initializing RAG systems on Django startup...")
            rag_manager.initialize_rag_systems()
            logger.info("✅ RAG systems initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG systems: {str(e)}")
            # Don't raise the exception to allow Django to start
            # The RAG system will fall back to basic responses if needed


        # Note: DB systems are now initialized through rag_manager.initialize_rag_systems()
        # No need for separate db_handler.initialize() call
