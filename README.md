# MSR Protocol Integration Project

## Overview
This project implements a real-time data visualization system for MSR (Modular Signal Recorder) protocol data. It establishes TCP communication with an EtherLab server, processes the incoming data, and displays it in a web-based dashboard using Django and WebSockets.

## Features
- Asynchronous TCP communication with EtherLab server on port 2345
- Real-time data processing and visualization
- WebSocket-based data streaming to the frontend
- Interactive dashboard with Chart.js for data visualization
- Django-based web application with Channels for WebSocket support

## Technology Stack
- **Backend**: Django 5.2, Channels 4.2.2
- **Frontend**: HTML, JavaScript, Chart.js
- **Communication**: WebSockets, TCP Sockets
- **Server**: Uvicorn ASGI server
- **API**: Django REST Framework

## Project Structure
```
msr_project/
├── manage.py
├── msr_project/          # Main Django project
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── msr_control/          # Django app for MSR control
│   ├── apps.py
│   ├── consumers.py      # WebSocket consumers
│   ├── msr_protocol.py   # MSR protocol implementation
│   ├── routing.py        # WebSocket routing
│   ├── tasks.py          # Background tasks
│   ├── urls.py
│   └── views.py
└── templates/            # HTML templates
    └── msr_control/
        └── dashboard.html
```

## Installation

### Prerequisites
- Python 3.10 or higher
- Docker (optional, for EtherLab setup)

### Setup
1. Clone the repository:
   ```
   git clone <repository-url>
   cd msr-protocol-integration-challange
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   cd msr_project
   python manage.py migrate
   ```

### Running the Application
1. Start the Django development server:
   ```
   python manage.py runserver
   ```

2. Access the dashboard at:
   ```
   http://127.0.0.1:8000/msr_control/dashboard/
   ```

## EtherLab Setup (Optional)
A Dockerfile is provided to set up the EtherLab environment:

```
docker build -t etherlab .
docker run -p 2345:2345 etherlab
```

## Usage
1. Start the Django server
2. The application will automatically attempt to connect to the EtherLab server
3. Visit the dashboard to view real-time data visualization
4. Data is automatically updated via WebSockets

## Project Working Flow

### Data Flow Architecture
```
+----------------+      +----------------+      +----------------+
|                |      |                |      |                |
|  EtherLab      | TCP  |  Django        | WS   |  Web Browser   |
|  Server        |----->|  Application   |----->|  Dashboard     |
|  (Port 2345)   |      |  (ASGI)        |      |  (Chart.js)    |
|                |      |                |      |                |
+----------------+      +----------------+      +----------------+
```

### Detailed Flow
1. **Data Acquisition**
   - The EtherLab server collects MSR protocol data
   - Data is made available via TCP on port 2345

2. **Backend Processing**
   - `msr_protocol.py` establishes an asynchronous TCP connection to the EtherLab server
   - The connection is managed by `connect_to_etherlab()` function
   - Incoming data is processed asynchronously by `process_data()` function

3. **Background Task Management**
   - `tasks.py` contains the `fetch_msr_data()` function that runs as a background task
   - This task is automatically started when the Django application initializes
   - The task periodically fetches data from the EtherLab server

4. **WebSocket Communication**
   - Processed data is sent to the WebSocket layer via `send_data_to_websocket()` function
   - Django Channels manages the WebSocket connections through the ASGI interface
   - `MSRConsumer` class in `consumers.py` handles WebSocket events and data distribution

5. **Frontend Visualization**
   - The dashboard HTML template contains JavaScript code that establishes a WebSocket connection
   - When new data arrives via WebSocket, the `onmessage` event handler is triggered
   - Chart.js is used to visualize the data in real-time
   - The chart is continuously updated as new data arrives

### Sequence of Operations
1. User starts the Django server
2. Django initializes and starts the background task for data fetching
3. The background task establishes a TCP connection to the EtherLab server
4. User opens the dashboard in a web browser
5. Browser establishes a WebSocket connection to the Django server
6. EtherLab server sends MSR data over TCP
7. Django processes the data and forwards it over WebSocket
8. Browser receives the data and updates the chart visualization in real-time

## Development

### Adding New Features
1. Implement new data processing in `msr_protocol.py`
2. Update the WebSocket consumer in `consumers.py` if needed
3. Modify the dashboard template for new visualizations

### Testing
Run the Django test suite:
```
python manage.py test
```

## License
[Specify your license here]

## Contributors
[Your name/organization]
