# MSR Protocol Integration - User Roles and Permissions

This document provides detailed information about the user roles and permissions implemented in the MSR Protocol Integration project.

## Overview

The system implements a role-based access control (RBAC) model with three predefined user roles:

1. **Operator**: Basic monitoring capabilities
2. **Calibrator**: Intermediate access with calibration permissions
3. **Admin**: Full system access with administrative privileges

Each role has specific permissions and access to different features of the application.

## Role Definitions

### Operator Role

The Operator role is designed for users who need to monitor the system but don't need to make changes to its configuration.

**Permissions**:
- View the dashboard
- See real-time data visualization
- View basic system status
- Access operator-specific views

**Restrictions**:
- Cannot access calibration controls
- Cannot view raw data or calibration parameters
- Cannot access administrative features
- Cannot modify system settings

**Data Access**:
- Filtered data with only essential information
- No access to raw data or internal system information
- Limited connection status information

### Calibrator Role

The Calibrator role is designed for users who need to adjust calibration parameters and monitor the system in more detail.

**Permissions**:
- All Operator permissions
- Access to calibration controls
- Ability to adjust data processing parameters
- View raw and calibrated data
- Access calibrator-specific views

**Restrictions**:
- Cannot access administrative features
- Cannot modify system settings
- Cannot manage users

**Data Access**:
- More detailed data including raw values
- Calibration parameters and settings
- More detailed connection status information
- No access to administrative data

### Admin Role

The Admin role has full access to all features of the system, including administrative functions.

**Permissions**:
- All Calibrator permissions
- User management (create, edit, delete users)
- System settings configuration
- Access to system logs and diagnostics
- Service control (restart, configure)
- Access to admin-specific views

**Restrictions**:
- None (full access)

**Data Access**:
- Complete, unfiltered data
- All system parameters and settings
- Full connection status and error information
- Administrative data and statistics

## Implementation Details

### Database Model

The user roles are implemented using a `UserRole` model that extends Django's built-in User model:

```python
class UserRole(models.Model):
    ROLE_CHOICES = (
        ('operator', 'Operator'),
        ('calibrator', 'Calibrator'),
        ('admin', 'Admin'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator')
    
    # Helper properties
    @property
    def is_operator(self):
        return self.role == 'operator'
    
    @property
    def is_calibrator(self):
        return self.role == 'calibrator'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
```

### Authentication and Role Assignment

When a user registers, they select a role which is then assigned to their account:

```python
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save()
            
            # Create the user role
            role = form.cleaned_data.get('role')
            UserRole.objects.create(user=user, role=role)
            
            # Log the user in
            # ...
```

### Permission Checks

Permissions are checked at multiple levels:

1. **View-Level Checks**:
   ```python
   @login_required
   def calibrator_view(request):
       # Check if user has calibrator role or higher
       try:
           user_role = request.user.role
           if not (user_role.is_calibrator or user_role.is_admin):
               return HttpResponseForbidden("You don't have permission to access this page")
       except UserRole.DoesNotExist:
           return HttpResponseForbidden("Role not assigned")
       
       return render(request, 'msr_control/calibrator.html')
   ```

2. **WebSocket-Level Checks**:
   ```python
   async def receive(self, text_data):
       # ...
       if action == 'calibrate':
           if not (self.user_role in ['calibrator', 'admin']):
               await self.send(text_data=json.dumps({
                   'error': 'Permission denied. Calibration requires Calibrator or Admin role.'
               }))
               return
   ```

3. **Template-Level Checks**:
   ```html
   {% if user_role == 'calibrator' or user_role == 'admin' %}
       <div class="tab" data-tab="calibration">Calibration</div>
   {% endif %}
   ```

### Data Filtering

Data sent to clients is filtered based on their role:

```python
@database_sync_to_async
def filter_data_by_role(self, data):
    if not isinstance(data, dict):
        return data
        
    try:
        # Create a copy to avoid modifying the original
        filtered_data = data.copy()
        
        if self.user_role == 'operator':
            # Operators only see basic data
            if 'admin_data' in filtered_data:
                del filtered_data['admin_data']
            if 'calibration_data' in filtered_data:
                del filtered_data['calibration_data']
            # Simplify connection state for operators
            if 'connection_state' in filtered_data:
                filtered_data['connection_state'] = {
                    'connected': filtered_data['connection_state'].get('connected', False)
                }
                
        elif self.user_role == 'calibrator':
            # Calibrators see everything except admin data
            if 'admin_data' in filtered_data:
                del filtered_data['admin_data']
                
        # Admin sees everything (no filtering needed)
        
        return filtered_data
        
    except Exception as e:
        logger.error(f"Error filtering data: {str(e)}")
        # Return basic data on error to avoid leaking sensitive information
        return {
            'timestamp': data.get('timestamp'),
            'filtered_value': data.get('filtered_value'),
            'error': 'Error filtering data'
        }
```

## User Interface

The user interface adapts based on the user's role:

### Dashboard

The dashboard shows different tabs and controls based on the user's role:

- **All Users**: See the Monitoring tab with real-time data visualization
- **Calibrators and Admins**: Also see the Calibration tab with calibration controls
- **Admins Only**: Also see User Management and System Settings tabs

### Navigation

The navigation menu shows different options based on the user's role:

- **Operators**: See basic navigation options
- **Calibrators**: See additional calibration-related options
- **Admins**: See all navigation options including administrative functions

### Controls

Different controls are available based on the user's role:

- **Operators**: View-only controls for monitoring
- **Calibrators**: Calibration controls for adjusting parameters
- **Admins**: All controls including system configuration and user management

## Default Users

The system creates default users for each role during initialization:

- **Admin**: username=admin, password=admin123
- **Calibrator**: username=calibrator, password=calibrator123
- **Operator**: username=operator, password=operator123

These default users can be used for testing and initial setup.

## Extending the Role System

To add a new role or modify existing roles:

1. Update the `ROLE_CHOICES` tuple in the `UserRole` model
2. Create a migration for the model change
3. Update permission checks in views and WebSocket consumers
4. Update templates to show role-specific UI elements
5. Update data filtering logic in the WebSocket consumer

## Best Practices

When working with the role system:

1. Always check permissions before performing sensitive operations
2. Filter data based on the user's role to prevent information leakage
3. Use the built-in helper properties (`is_operator`, `is_calibrator`, `is_admin`) for role checks
4. Consider the principle of least privilege when assigning permissions to roles
5. Test with different user roles to ensure proper access control
