import asyncio
import socket

async def connect_to_etherlab():
    host = '127.0.0.1'  # EtherLab's IP address
    port = 2345

    loop = asyncio.get_event_loop()
    
    # Create a non-blocking socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(False)  # Set socket to non-blocking
    
    # Connect the socket asynchronously
    await loop.sock_connect(s, (host, port))

    try:
        while True:
            # Receive data asynchronously (non-blocking)
            data = await loop.sock_recv(s, 1024)  # Buffer size (adjust if needed)
            if not data:
                break
            await process_data(data)
    finally:
        s.close()

async def process_data(data):
    # Process the MSR data asynchronously and send it for visualization
    print("Received data:", data)
    # You can pass this data to your WebSocket consumer here
    # await send_data_to_websocket(data)
