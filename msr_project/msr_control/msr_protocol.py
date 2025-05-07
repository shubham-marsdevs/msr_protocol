"""
MSR Protocol implementation for communicating with the EtherLab server.

This module handles the TCP connection to the EtherLab server, processes the
incoming data, and sends it to the WebSocket layer for real-time visualization.
"""
import asyncio
import socket
import json
import random
import time
from channels.layers import get_channel_layer
from django.conf import settings

# Try to import the logger, but don't fail if it's not available yet
try:
    from .utils.logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Default calibration settings
DEFAULT_CALIBRATION_SETTINGS = {
    'offset': 0.0,
    'gain': 1.0,
    'filter': 0.5
}

# Default connection settings
DEFAULT_CONNECTION_SETTINGS = {
    'host': '127.0.0.1',
    'port': 2345,
    'timeout': 30,
    'retry_attempts': 3,
    'buffer_size': 1024,
    'reconnect_delay': 5  # seconds to wait before reconnecting
}

# Global settings (initialized with defaults)
calibration_settings = DEFAULT_CALIBRATION_SETTINGS.copy()
connection_settings = DEFAULT_CONNECTION_SETTINGS.copy()

# Connection state tracking
connection_state = {
    'connected': False,
    'last_connected': None,
    'reconnect_attempts': 0,
    'last_error': None
}

async def connect_to_etherlab():
    """
    Establishes a TCP connection to the EtherLab server and processes incoming data.

    This function handles connection establishment, data reception, and error recovery.
    If the connection fails, it will attempt to reconnect based on the retry settings.
    """
    global connection_state

    host = connection_settings['host']
    port = connection_settings['port']
    buffer_size = connection_settings['buffer_size']
    max_retries = connection_settings['retry_attempts']
    reconnect_delay = connection_settings['reconnect_delay']

    logger.info(f"Connecting to EtherLab server at {host}:{port}")

    # Update connection state
    connection_state['reconnect_attempts'] += 1

    # Get the event loop
    loop = asyncio.get_event_loop()

    # Create a socket with timeout
    s = None

    try:
        # Create a non-blocking socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)  # Set socket to non-blocking

        # Connect the socket asynchronously with timeout
        try:
            # Set a timeout for the connection attempt
            connect_task = loop.sock_connect(s, (host, port))
            await asyncio.wait_for(connect_task, timeout=connection_settings['timeout'])

            # Update connection state on successful connection
            connection_state['connected'] = True
            connection_state['last_connected'] = time.time()
            connection_state['reconnect_attempts'] = 0
            connection_state['last_error'] = None

            logger.info(f"Successfully connected to EtherLab server at {host}:{port}")

            # Process data in a loop
            while True:
                try:
                    # Receive data asynchronously with timeout
                    data_task = loop.sock_recv(s, buffer_size)
                    data = await asyncio.wait_for(data_task, timeout=connection_settings['timeout'])

                    if not data:
                        logger.warning("Received empty data, connection may be closed")
                        break

                    # Process the data and send it to WebSocket
                    processed_data = await process_data(data)
                    await send_data_to_websocket(processed_data)

                except asyncio.TimeoutError:
                    logger.warning("Timeout while receiving data")
                    # Send a heartbeat to check if the connection is still alive
                    try:
                        s.send(b'\x00')  # Send a null byte as heartbeat
                    except (BlockingIOError, ConnectionError):
                        logger.error("Connection lost during heartbeat")
                        break

                except Exception as e:
                    logger.error(f"Error while processing data: {str(e)}")
                    break

        except asyncio.TimeoutError:
            logger.error(f"Connection timeout after {connection_settings['timeout']} seconds")
            connection_state['last_error'] = "Connection timeout"
            raise ConnectionError("Connection timeout")

    except (ConnectionRefusedError, ConnectionError, OSError) as e:
        # Update connection state on failure
        connection_state['connected'] = False
        connection_state['last_error'] = str(e)

        logger.error(f"Connection error: {str(e)}")

        # Decide whether to retry or use demo data
        if connection_state['reconnect_attempts'] <= max_retries:
            logger.info(f"Reconnecting in {reconnect_delay} seconds (attempt {connection_state['reconnect_attempts']} of {max_retries})")
            await asyncio.sleep(reconnect_delay)
            asyncio.create_task(connect_to_etherlab())
        else:
            logger.warning(f"Max reconnection attempts reached ({max_retries}), switching to demo data")
            # For demo purposes, generate random data if connection fails
            asyncio.create_task(generate_demo_data())

    finally:
        # Clean up the socket
        if s:
            try:
                s.close()
                logger.info("Socket closed")
            except Exception as e:
                logger.error(f"Error closing socket: {str(e)}")

async def process_data(data):
    """
    Process the MSR data with calibration settings applied.

    Args:
        data: Raw binary data received from the EtherLab server

    Returns:
        dict: Processed data structure with various levels of detail for different roles
    """
    try:
        # For demonstration, convert bytes to a simple numeric value
        # In a real application, you would parse the MSR protocol data properly
        if not data:
            raise ValueError("Empty data received")

        # Basic data validation
        if not isinstance(data, bytes):
            data = bytes(data)

        # Parse the data (simplified for demonstration)
        raw_value = sum(data) / len(data)

        # Apply calibration with bounds checking
        try:
            offset = float(calibration_settings.get('offset', 0.0))
            gain = float(calibration_settings.get('gain', 1.0))
            filter_val = float(calibration_settings.get('filter', 0.5))

            # Ensure gain is not zero to avoid division by zero
            if gain == 0:
                gain = 1.0
                logger.warning("Gain was set to zero, defaulting to 1.0")

            # Ensure filter is between 0 and 1
            filter_val = max(0.0, min(1.0, filter_val))

            # Apply calibration
            calibrated_value = (raw_value + offset) * gain

        except (ValueError, TypeError) as e:
            logger.error(f"Calibration error: {str(e)}")
            # Use default values if calibration fails
            calibrated_value = raw_value

        # Apply filtering (simple low-pass filter for demonstration)
        # Store last value in a class variable for persistence
        last_value = getattr(process_data, 'last_value', None)

        if last_value is not None:
            filtered_value = (filter_val * calibrated_value +
                             (1 - filter_val) * last_value)
        else:
            filtered_value = calibrated_value

        # Update the last value
        process_data.last_value = filtered_value

        # Get current timestamp
        current_time = time.time()

        # Create a data structure with different levels of detail for different roles
        processed_data = {
            'timestamp': current_time,
            'raw_value': raw_value,  # Only visible to calibrators and admins
            'calibrated_value': calibrated_value,  # Visible to all
            'filtered_value': filtered_value,  # Visible to all
            'calibration_data': {  # Only visible to calibrators and admins
                'offset': calibration_settings['offset'],
                'gain': calibration_settings['gain'],
                'filter': calibration_settings['filter']
            },
            'connection_state': {  # Connection status information
                'connected': connection_state['connected'],
                'last_connected': connection_state['last_connected'],
                'reconnect_attempts': connection_state['reconnect_attempts']
            },
            'admin_data': {  # Only visible to admins
                'connection_info': {
                    'host': connection_settings['host'],
                    'port': connection_settings['port'],
                    'buffer_size': connection_settings['buffer_size']
                },
                'system_stats': {
                    'memory_usage': random.randint(10, 90),  # Mock data
                    'cpu_usage': random.randint(5, 80)  # Mock data
                }
            }
        }

        logger.debug(f"Processed data: raw={raw_value:.2f}, calibrated={calibrated_value:.2f}, filtered={filtered_value:.2f}")
        return processed_data

    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return {
            'timestamp': time.time(),
            'error': str(e),
            'connection_state': {
                'connected': connection_state['connected'],
                'last_connected': connection_state['last_connected'],
                'reconnect_attempts': connection_state['reconnect_attempts'],
                'last_error': connection_state['last_error']
            }
        }

async def send_data_to_websocket(data):
    """
    Send the processed data to the frontend via WebSockets.

    Args:
        data: Processed data dictionary to send to clients
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.error("Channel layer not available")
            return

        await channel_layer.group_send(
            "msr_data",  # WebSocket group name
            {
                "type": "send_data",  # This triggers the send_data method in the WebSocket consumer
                "data": data,
            }
        )
        logger.debug("Data sent to WebSocket")
    except Exception as e:
        logger.error(f"Error sending data to WebSocket: {str(e)}")

async def generate_demo_data():
    """
    Generate demo data for testing when no real connection is available.

    This function runs in an infinite loop, generating random data points
    that simulate real MSR data from the EtherLab server.
    """
    logger.info("Starting demo data generation")

    # Update connection state to indicate we're using demo data
    connection_state['connected'] = False
    connection_state['last_error'] = "Using demo data"

    # Initialize trend simulation variables
    trend_direction = 1  # 1 for up, -1 for down
    trend_duration = 0
    max_trend_duration = 10  # Maximum number of steps in one direction
    noise_level = 5.0  # Amount of random noise to add

    # Starting value
    base_value = 50.0

    try:
        while True:
            await asyncio.sleep(1)  # Generate data every second

            # Determine if we should change trend direction
            trend_duration += 1
            if trend_duration >= max_trend_duration:
                trend_direction *= -1  # Reverse direction
                trend_duration = 0
                max_trend_duration = random.randint(5, 15)  # Randomize next trend duration

            # Create semi-realistic trending data with noise
            trend_component = trend_direction * random.uniform(0.5, 2.0)
            noise_component = random.uniform(-noise_level, noise_level)

            # Update base value with trend and noise
            base_value += trend_component + noise_component

            # Keep values within reasonable bounds
            base_value = max(10.0, min(base_value, 100.0))

            # Use the base value as our raw value
            raw_value = base_value

            # Apply calibration with error handling
            try:
                offset = float(calibration_settings.get('offset', 0.0))
                gain = float(calibration_settings.get('gain', 1.0))
                filter_val = float(calibration_settings.get('filter', 0.5))

                # Ensure gain is not zero
                if gain == 0:
                    gain = 1.0

                # Ensure filter is between 0 and 1
                filter_val = max(0.0, min(1.0, filter_val))

                # Apply calibration
                calibrated_value = (raw_value + offset) * gain

            except (ValueError, TypeError) as e:
                logger.error(f"Demo data calibration error: {str(e)}")
                calibrated_value = raw_value

            # Apply filtering
            last_value = getattr(generate_demo_data, 'last_value', None)
            if last_value is not None:
                filtered_value = (filter_val * calibrated_value +
                                 (1 - filter_val) * last_value)
            else:
                filtered_value = calibrated_value

            # Update the last value
            generate_demo_data.last_value = filtered_value

            # Get current timestamp
            current_time = time.time()

            # Create a data structure with different levels of detail for different roles
            processed_data = {
                'timestamp': current_time,
                'raw_value': raw_value,
                'calibrated_value': calibrated_value,
                'filtered_value': filtered_value,
                'is_demo_data': True,  # Flag to indicate this is demo data
                'calibration_data': {
                    'offset': calibration_settings['offset'],
                    'gain': calibration_settings['gain'],
                    'filter': calibration_settings['filter']
                },
                'connection_state': {
                    'connected': False,
                    'last_connected': connection_state['last_connected'],
                    'reconnect_attempts': connection_state['reconnect_attempts'],
                    'last_error': connection_state['last_error']
                },
                'admin_data': {
                    'connection_info': {
                        'host': connection_settings['host'],
                        'port': connection_settings['port'],
                        'buffer_size': connection_settings['buffer_size']
                    },
                    'system_stats': {
                        'memory_usage': random.randint(10, 90),
                        'cpu_usage': random.randint(5, 80)
                    }
                }
            }

            # Send the demo data to WebSocket
            await send_data_to_websocket(processed_data)
            logger.debug(f"Generated demo data: raw={raw_value:.2f}, filtered={filtered_value:.2f}")

    except asyncio.CancelledError:
        logger.info("Demo data generation cancelled")
    except Exception as e:
        logger.error(f"Error in demo data generation: {str(e)}")
        # Try to restart the demo data generation
        asyncio.create_task(generate_demo_data())

async def update_calibration(new_settings):
    """
    Update the calibration settings.

    Args:
        new_settings: Dictionary containing the new calibration settings

    Returns:
        dict: Updated calibration settings
    """
    global calibration_settings

    logger.info(f"Updating calibration settings: {new_settings}")

    try:
        # Validate the new settings
        if not isinstance(new_settings, dict):
            raise ValueError("Settings must be a dictionary")

        # Update only the provided settings with validation
        for key, value in new_settings.items():
            if key not in calibration_settings:
                logger.warning(f"Unknown calibration setting: {key}")
                continue

            # Type checking and validation
            if key == 'offset':
                calibration_settings[key] = float(value)
            elif key == 'gain':
                # Ensure gain is not zero
                gain_value = float(value)
                if gain_value == 0:
                    logger.warning("Gain cannot be zero, setting to 1.0")
                    calibration_settings[key] = 1.0
                else:
                    calibration_settings[key] = gain_value
            elif key == 'filter':
                # Ensure filter is between 0 and 1
                filter_value = float(value)
                calibration_settings[key] = max(0.0, min(1.0, filter_value))
            else:
                calibration_settings[key] = value

        logger.info(f"Calibration settings updated: {calibration_settings}")
        return calibration_settings

    except Exception as e:
        logger.error(f"Error updating calibration settings: {str(e)}")
        return {
            'error': str(e),
            'current_settings': calibration_settings
        }

async def update_connection_settings(new_settings):
    """
    Update the connection settings.

    Args:
        new_settings: Dictionary containing the new connection settings

    Returns:
        dict: Updated connection settings
    """
    global connection_settings

    logger.info(f"Updating connection settings: {new_settings}")

    try:
        # Validate the new settings
        if not isinstance(new_settings, dict):
            raise ValueError("Settings must be a dictionary")

        # Store original settings in case we need to revert
        original_settings = connection_settings.copy()

        # Update only the provided settings with validation
        for key, value in new_settings.items():
            if key not in connection_settings:
                logger.warning(f"Unknown connection setting: {key}")
                continue

            # Type checking and validation
            if key in ['port', 'buffer_size', 'timeout', 'retry_attempts', 'reconnect_delay']:
                # These should be integers and positive
                int_value = int(value)
                if int_value <= 0:
                    logger.warning(f"{key} must be positive, ignoring value: {value}")
                    continue
                connection_settings[key] = int_value
            elif key == 'host':
                # Basic validation for hostname/IP
                if not isinstance(value, str) or not value.strip():
                    logger.warning(f"Invalid host value: {value}")
                    continue
                connection_settings[key] = value
            else:
                connection_settings[key] = value

        logger.info(f"Connection settings updated: {connection_settings}")

        # If host or port changed, we might want to reconnect
        if (original_settings['host'] != connection_settings['host'] or
            original_settings['port'] != connection_settings['port']):
            logger.info("Host or port changed, reconnection may be required")

        return connection_settings

    except Exception as e:
        logger.error(f"Error updating connection settings: {str(e)}")
        return {
            'error': str(e),
            'current_settings': connection_settings
        }
