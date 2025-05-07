import asyncio
from msr_control.msr_protocol import connect_to_etherlab

# This is your background task that fetches MSR data
async def fetch_msr_data():
    """
    Background task that connects to the EtherLab server and fetches MSR data.
    The connect_to_etherlab function now handles both data processing and sending to WebSocket.
    """
    try:
        # Connect to EtherLab server and start processing data
        await connect_to_etherlab()
    except Exception as e:
        print(f"Error in fetch_msr_data task: {e}")
        # Wait a bit before retrying
        await asyncio.sleep(5)
        # Restart the task
        asyncio.create_task(fetch_msr_data())
