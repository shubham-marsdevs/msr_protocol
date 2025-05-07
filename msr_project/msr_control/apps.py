"""
Django application configuration for MSR Control.

This module contains the Django AppConfig for the MSR Control application,
including initialization of background tasks.
"""
import os
import sys
import asyncio
import threading
from django.apps import AppConfig

# Try to import the logger, but don't fail if it's not available yet
try:
    from .utils.logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class MsrControlConfig(AppConfig):
    """
    Django AppConfig for the MSR Control application.

    This class handles the initialization of the application, including
    starting background tasks for data fetching.
    """
    name = 'msr_control'
    verbose_name = 'MSR Protocol Control'

    def ready(self):
        """
        Initialize the application when Django is ready.

        This method is called by Django when the application is initialized.
        It starts the background task for fetching MSR data.
        """
        # Avoid running the background task in management commands
        if 'runserver' not in sys.argv and 'daphne' not in sys.argv:
            return

        # Avoid running in multiple processes (e.g., when using runserver with autoreload)
        if os.environ.get('RUN_MAIN') != 'true' and 'daphne' not in sys.argv:
            return

        logger.info("Initializing MSR Control application")

        # Import here to avoid circular imports
        from .tasks import fetch_msr_data

        # Start the background task in the event loop
        try:
            loop = asyncio.get_event_loop()

            # Check if the loop is running
            if loop.is_running():
                # Create the task in the running loop
                logger.info("Starting background task in running event loop")
                asyncio.create_task(fetch_msr_data())
            else:
                # Start a new thread to run the event loop
                logger.info("Starting background task in new thread")
                self._start_background_thread(fetch_msr_data)

            logger.info("MSR Control application initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing MSR Control application: {str(e)}")

    def _start_background_thread(self, task_func):
        """
        Start a background thread to run the event loop and task.

        Args:
            task_func: The async function to run in the background
        """
        def run_event_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.create_task(task_func())
                loop.run_forever()
            except Exception as e:
                logger.error(f"Error in background thread: {str(e)}")
            finally:
                loop.close()

        # Start the thread
        thread = threading.Thread(target=run_event_loop, daemon=True)
        thread.start()
