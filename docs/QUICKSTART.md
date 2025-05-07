# MSR Protocol Integration - Quick Start Guide

This guide provides step-by-step instructions for getting started with the MSR Protocol Integration project as a developer.

## Prerequisites

- Python 3.8 or higher
- Git
- Redis (for Channels)
- Basic knowledge of Django, WebSockets, and asyncio

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/msr-protocol-integration.git
cd msr-protocol-integration
```

### 2. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply Migrations

```bash
cd msr_project
python manage.py migrate
```

### 5. Run the Development Server

```bash
python manage.py runserver
```

### 6. Access the Application

- Login page: http://127.0.0.1:8000/msr_control/login/
- Default users:
  - Admin: username=admin, password=admin123
  - Calibrator: username=calibrator, password=calibrator123
  - Operator: username=operator, password=operator123

## Development Workflow

### Understanding the Code Structure

The project follows a modular structure:

- `msr_protocol.py`: Handles TCP communication with the EtherLab server
- `consumers.py`: WebSocket consumers for real-time data streaming
- `tasks.py`: Background tasks for data fetching
- `views.py`: HTTP views for the web interface
- `models.py`: Data models including UserRole
- `templates/`: HTML templates for the web interface

### Making Changes

1. **Modifying the MSR Protocol Implementation**:
   - Edit `msr_control/msr_protocol.py` to change how data is processed
   - Update the `process_data` function to modify data processing logic

2. **Updating the Web Interface**:
   - Edit templates in `templates/msr_control/` to change the UI
   - Modify `dashboard.html` for the main dashboard
   - Update role-specific templates for different user roles

3. **Changing User Roles and Permissions**:
   - Edit `models.py` to modify the UserRole model
   - Update the WebSocket consumer in `consumers.py` to change permission checks
   - Modify views in `views.py` to update HTTP endpoint permissions

### Testing Your Changes

1. **Manual Testing**:
   - Run the development server: `python manage.py runserver`
   - Log in with different user roles to test permissions
   - Check the real-time data visualization

2. **Automated Testing**:
   - Run the test suite: `python manage.py test`
   - Add new tests in `tests.py` for your changes

## Common Tasks

### Adding a New User Role

1. Update the `ROLE_CHOICES` tuple in the `UserRole` model:

```python
# msr_control/models.py
class UserRole(models.Model):
    ROLE_CHOICES = (
        ('operator', 'Operator'),
        ('calibrator', 'Calibrator'),
        ('admin', 'Admin'),
        ('new_role', 'New Role'),  # Add your new role here
    )
    # ...
```

2. Create a migration for the model change:

```bash
python manage.py makemigrations
python manage.py migrate
```

3. Update permission checks in the WebSocket consumer:

```python
# msr_control/consumers.py
async def receive(self, text_data):
    # ...
    if action == 'some_action':
        if not (self.user_role in ['calibrator', 'admin', 'new_role']):
            # Permission denied
            # ...
```

4. Update the dashboard template to show role-specific UI:

```html
<!-- templates/msr_control/dashboard.html -->
{% if user_role == 'new_role' or user_role == 'admin' %}
    <!-- UI elements for the new role -->
{% endif %}
```

### Adding a New Feature

1. Implement the backend logic in the appropriate module
2. Update the WebSocket consumer to handle new commands
3. Add the UI elements to the templates
4. Update permission checks for the new feature

### Troubleshooting

- **WebSocket Connection Issues**:
  - Check the browser console for WebSocket errors
  - Verify that the WebSocket URL is correct
  - Ensure the user is authenticated

- **Data Processing Issues**:
  - Check the logs in `logs/msr_control.log`
  - Add debug logging to trace the data flow
  - Verify the TCP connection to the EtherLab server

- **Permission Issues**:
  - Verify the user's role in the database
  - Check the permission checks in the WebSocket consumer
  - Ensure the user is properly authenticated

## Next Steps

After getting familiar with the codebase, you might want to:

1. Implement new data processing features
2. Add more visualization options
3. Enhance the user management interface
4. Improve error handling and logging
5. Add more automated tests

For more detailed information, refer to the [Implementation Documentation](IMPLEMENTATION.md).

## Getting Help

If you encounter any issues or have questions, please:

1. Check the logs in the `logs/` directory
2. Review the [Implementation Documentation](IMPLEMENTATION.md)
3. Contact the project maintainers
