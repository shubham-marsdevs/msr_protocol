"""
Background tasks for the MSR Control application.

This module contains asynchronous background tasks that run
independently of the HTTP request/response cycle.
"""
import asyncio
import traceback
from msr_control.msr_protocol import connect_to_etherlab

# Try to import the logger, but don't fail if it's not available yet
try:
    from .utils.logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

async def fetch_msr_data():
    """
    Background task that connects to the EtherLab server and fetches MSR data.

    This task runs continuously in the background, connecting to the EtherLab server,
    processing the received data, and sending it to WebSocket clients. If the connection
    fails, it will attempt to reconnect based on the configured retry settings.
    """
    logger.info("Starting MSR data fetch task")

    # Track consecutive failures for exponential backoff
    consecutive_failures = 0
    max_backoff = 60  # Maximum backoff time in seconds

    while True:
        try:
            # Connect to EtherLab server and start processing data
            logger.info("Connecting to EtherLab server")
            await connect_to_etherlab()

            # If we get here, the connection has been closed normally
            # Reset consecutive failures counter
            consecutive_failures = 0
            logger.info("Connection to EtherLab server closed normally")

        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            logger.info("MSR data fetch task cancelled")
            break

        except Exception as e:
            # Log the error with traceback
            logger.error(f"Error in fetch_msr_data task: {str(e)}")
            logger.debug(traceback.format_exc())

            # Increment consecutive failures counter
            consecutive_failures += 1

            # Calculate backoff time with exponential backoff and jitter
            backoff_time = min(2 ** consecutive_failures + (0.1 * asyncio.get_event_loop().time() % 1), max_backoff)

            logger.warning(f"Retrying in {backoff_time:.1f} seconds (attempt {consecutive_failures})")

            # Wait before retrying
            await asyncio.sleep(backoff_time)

        # Small delay to prevent tight loop in case of repeated immediate failures
        await asyncio.sleep(1)
