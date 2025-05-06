from django.apps import AppConfig
import asyncio
from .tasks import fetch_msr_data

class MsrControlConfig(AppConfig):
    name = 'msr_control'

    def ready(self):
        """Start the background task when the app is ready."""
        loop = asyncio.get_event_loop()
        loop.create_task(fetch_msr_data())  # Start the async background task
