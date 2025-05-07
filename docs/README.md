# MSR Protocol Integration Project

## Overview

The MSR Protocol Integration project is a Django-based web application that connects to an EtherLab server via the MSR protocol, processes the data in real-time, and provides a web interface for visualization and control. The system implements role-based access control with three user roles (Operator, Calibrator, Admin) and provides role-specific features and permissions.

## Key Features

- **Real-time Data Processing**: Asynchronous TCP communication with the EtherLab server
- **WebSocket Communication**: Real-time data streaming to the frontend
- **Role-Based Access Control**: Three user roles with different permissions
- **Interactive Dashboard**: Real-time data visualization with Chart.js
- **Calibration Controls**: Parameter adjustment for data processing
- **User Management**: Admin interface for user administration
- **Security Features**: Comprehensive security measures for production use
- **Error Handling and Logging**: Robust error recovery and detailed logging

## User Roles

The system implements three user roles with different permission levels:

1. **Operator**: Basic monitoring capabilities
   - View real-time data visualization
   - Access to basic system status

2. **Calibrator**: Intermediate access level
   - All Operator permissions
   - Access to calibration controls
   - Ability to adjust data processing parameters

3. **Admin**: Full system access
   - All Calibrator permissions
   - User management
   - System settings configuration
   - Service control

## Technical Stack

- **Backend**: Django, Channels, asyncio
- **Frontend**: HTML, CSS, JavaScript, Chart.js
- **Communication**: WebSockets, TCP
- **Data Processing**: Custom MSR protocol implementation

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Django 4.2 or higher
- Redis (for Channels)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/msr-protocol-integration.git
   cd msr-protocol-integration
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

4. Apply migrations:
   ```
   cd msr_project
   python manage.py migrate
   ```

5. Run the development server:
   ```
   python manage.py runserver
   ```

6. Access the application:
   - Login page: http://127.0.0.1:8000/msr_control/login/
   - Default users:
     - Admin: username=admin, password=admin123
     - Calibrator: username=calibrator, password=calibrator123
     - Operator: username=operator, password=operator123

## Documentation

For detailed implementation documentation, see [IMPLEMENTATION.md](IMPLEMENTATION.md).

## Project Structure

```
msr_project/
├── manage.py
├── msr_project/          # Main Django project
│   ├── asgi.py
│   ├── settings.py
│   ├── settings_prod.py  # Production settings
│   ├── urls.py
│   └── wsgi.py
├── msr_control/          # Django app for MSR control
│   ├── admin.py          # Admin site configuration
│   ├── apps.py           # App configuration with background tasks
│   ├── consumers.py      # WebSocket consumers
│   ├── forms.py          # Authentication forms
│   ├── middleware.py     # Security and logging middleware
│   ├── migrations/       # Database migrations
│   ├── models.py         # Data models including UserRole
│   ├── msr_protocol.py   # MSR protocol implementation
│   ├── routing.py        # WebSocket routing
│   ├── tasks.py          # Background tasks
│   ├── urls.py           # URL routing
│   ├── utils/            # Utility modules
│   │   ├── __init__.py
│   │   └── logger.py     # Logging utility
│   └── views.py          # View functions
└── templates/            # HTML templates
    └── msr_control/
        ├── admin.html    # Admin role template
        ├── calibrator.html # Calibrator role template
        ├── dashboard.html # Main dashboard
        ├── login.html    # Login page
        ├── operator.html # Operator role template
        └── signup.html   # User registration page
```

## Development

### Adding New Features

1. Implement new data processing in `msr_protocol.py`
2. Update the WebSocket consumer in `consumers.py` if needed
3. Modify the dashboard template for new visualizations

### Running Tests

```
python manage.py test
```

## Production Deployment

For production deployment, use the production settings:

```
python manage.py runserver --settings=msr_project.settings_prod
```

Make sure to set the following environment variables:
- `DJANGO_SECRET_KEY`: A secure secret key
- `ALLOWED_HOST`: The hostname of your server
- `DJANGO_DEBUG`: Set to 'False' for production

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django and Channels teams for the excellent frameworks
- Chart.js for the visualization library
