import asyncio
import socket
import json
import random
from channels.layers import get_channel_layer

# Global calibration settings
calibration_settings = {
    'offset': 0.0,
    'gain': 1.0,
    'filter': 0.5
}

# Global connection settings
connection_settings = {
    'host': '127.0.0.1',
    'port': 2345,
    'timeout': 30,
    'retry_attempts': 3,
    'buffer_size': 1024
}

async def connect_to_etherlab():
    host = connection_settings['host']
    port = connection_settings['port']
    buffer_size = connection_settings['buffer_size']

    loop = asyncio.get_event_loop()

    # Create a non-blocking socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(False)  # Set socket to non-blocking

    try:
        # Connect the socket asynchronously
        await loop.sock_connect(s, (host, port))

        while True:
            # Receive data asynchronously (non-blocking)
            data = await loop.sock_recv(s, buffer_size)
            if not data:
                break

            # Process the data and send it to WebSocket
            processed_data = await process_data(data)
            await send_data_to_websocket(processed_data)
    except (ConnectionRefusedError, OSError) as e:
        print(f"Connection error: {e}")
        # For demo purposes, generate random data if connection fails
        await generate_demo_data()
    finally:
        s.close()

async def process_data(data):
    """Process the MSR data with calibration settings applied"""
    try:
        # For demonstration, convert bytes to a simple numeric value
        # In a real application, you would parse the MSR protocol data properly
        raw_value = sum(data) / len(data)

        # Apply calibration
        calibrated_value = (raw_value + calibration_settings['offset']) * calibration_settings['gain']

        # Apply filtering (simple low-pass filter for demonstration)
        if hasattr(process_data, 'last_value'):
            filtered_value = (calibration_settings['filter'] * calibrated_value +
                             (1 - calibration_settings['filter']) * process_data.last_value)
        else:
            filtered_value = calibrated_value

        process_data.last_value = filtered_value

        # Create a data structure with different levels of detail for different roles
        processed_data = {
            'timestamp': asyncio.get_event_loop().time(),
            'raw_value': raw_value,  # Only visible to calibrators and admins
            'calibrated_value': calibrated_value,  # Visible to all
            'filtered_value': filtered_value,  # Visible to all
            'calibration_data': {  # Only visible to calibrators and admins
                'offset': calibration_settings['offset'],
                'gain': calibration_settings['gain'],
                'filter': calibration_settings['filter']
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

        return processed_data
    except Exception as e:
        print(f"Error processing data: {e}")
        return {'error': str(e)}

async def send_data_to_websocket(data):
    """Send the processed data to the frontend via WebSockets."""
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "msr_data",  # WebSocket group name
        {
            "type": "send_data",  # This triggers the send_data method in the WebSocket consumer
            "data": data,
        }
    )

async def generate_demo_data():
    """Generate demo data for testing when no real connection is available"""
    while True:
        await asyncio.sleep(1)  # Generate data every second

        # Create random data
        raw_value = random.uniform(10, 100)

        # Apply calibration
        calibrated_value = (raw_value + calibration_settings['offset']) * calibration_settings['gain']

        # Apply filtering
        if hasattr(generate_demo_data, 'last_value'):
            filtered_value = (calibration_settings['filter'] * calibrated_value +
                             (1 - calibration_settings['filter']) * generate_demo_data.last_value)
        else:
            filtered_value = calibrated_value

        generate_demo_data.last_value = filtered_value

        # Create a data structure with different levels of detail for different roles
        processed_data = {
            'timestamp': asyncio.get_event_loop().time(),
            'raw_value': raw_value,
            'calibrated_value': calibrated_value,
            'filtered_value': filtered_value,
            'calibration_data': {
                'offset': calibration_settings['offset'],
                'gain': calibration_settings['gain'],
                'filter': calibration_settings['filter']
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

        await send_data_to_websocket(processed_data)

async def update_calibration(new_settings):
    """Update the calibration settings"""
    global calibration_settings

    # Update only the provided settings
    for key, value in new_settings.items():
        if key in calibration_settings:
            calibration_settings[key] = value

    return calibration_settings

async def update_connection_settings(new_settings):
    """Update the connection settings"""
    global connection_settings

    # Update only the provided settings
    for key, value in new_settings.items():
        if key in connection_settings:
            connection_settings[key] = value

    return connection_settings
