import asyncio
from msr_control.msr_protocol import connect_to_etherlab
from channels.layers import get_channel_layer

# This is your background task that fetches MSR data
async def fetch_msr_data():
    while True:
        await asyncio.sleep(1)  # Adjust the interval as needed (currently 1 second)
        data = await connect_to_etherlab()  # Fetch data asynchronously
        await send_data_to_websocket(data)

# This function sends the data to the WebSocket using Django Channels
async def send_data_to_websocket(data):
    """Send the processed data to the frontend via WebSockets."""
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "msr_data",  # WebSocket group name (this must match the group in the consumer)
        {
            "type": "send_data",  # This triggers the send_data method in your WebSocket consumer
            "data": data,
        }
    )
