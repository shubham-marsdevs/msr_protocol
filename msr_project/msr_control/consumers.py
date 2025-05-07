"""
WebSocket consumers for the MSR Control application.

This module handles WebSocket connections for real-time data streaming
and bidirectional communication with the frontend.
"""
import json
import asyncio
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

# Try to import the logger, but don't fail if it's not available yet
try:
    from .utils.logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class MSRConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for MSR data streaming.

    This consumer handles real-time data streaming from the server to clients
    and processes commands from clients based on their roles.
    """

    async def connect(self):
        """
        Handle WebSocket connection.

        This method is called when a client attempts to establish a WebSocket connection.
        It performs authentication checks and sets up the connection.
        """
        self.room_name = "msr_data"
        self.room_group_name = f"msr_{self.room_name}"
        self.user = self.scope["user"]

        # Initialize user role
        self.user_role = None

        # Check if user is authenticated
        if self.user == AnonymousUser():
            logger.warning(f"Rejected unauthenticated WebSocket connection from {self.scope.get('client', ['Unknown'])[0]}")
            # Reject the connection if user is not authenticated
            await self.close(code=4001)  # Custom close code for authentication failure
            return

        try:
            # Get user role
            self.user_role = await self.get_user_role()

            # Join the WebSocket group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            # Accept the connection
            await self.accept()

            logger.info(f"WebSocket connection established for user {self.user.username} with role {self.user_role}")

            # Send initial connection status message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'user': self.user.username,
                'role': self.user_role
            }))

        except Exception as e:
            logger.error(f"Error during WebSocket connection: {str(e)}")
            # Print traceback for debugging
            traceback.print_exc()
            await self.close(code=4002)  # Custom close code for internal error

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        This method is called when a client disconnects from the WebSocket.
        It cleans up the connection and logs the event.

        Args:
            close_code: The code indicating why the connection was closed
        """
        try:
            # Leave the WebSocket group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            # Log the disconnection
            if hasattr(self, 'user') and self.user != AnonymousUser():
                logger.info(f"WebSocket disconnected for user {self.user.username} with code {close_code}")
            else:
                logger.info(f"WebSocket disconnected for anonymous user with code {close_code}")

        except Exception as e:
            logger.error(f"Error during WebSocket disconnection: {str(e)}")

    async def receive(self, text_data):
        """
        Handle incoming messages from WebSocket clients.

        This method processes commands and actions from clients based on their roles.

        Args:
            text_data: The JSON text data received from the client
        """
        try:
            # Parse the JSON data
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {self.user.username}: {text_data[:100]}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': 'Invalid JSON format'
                }))
                return

            # Log the received action
            action = data.get('action')
            logger.debug(f"Received action '{action}' from user {self.user.username}")

            # Process based on user role
            if action:
                # Check permissions based on role
                if action == 'calibrate':
                    if not (self.user_role in ['calibrator', 'admin']):
                        logger.warning(f"Permission denied: User {self.user.username} with role {self.user_role} attempted calibration")
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'error': 'Permission denied. Calibration requires Calibrator or Admin role.'
                        }))
                        return

                    # Process calibration action
                    await self.handle_calibration(data.get('parameters', {}))

                elif action == 'admin_action':
                    if self.user_role != 'admin':
                        logger.warning(f"Permission denied: User {self.user.username} with role {self.user_role} attempted admin action")
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'error': 'Permission denied. This action requires Admin role.'
                        }))
                        return

                    # Process admin action
                    command = data.get('command', '')
                    parameters = data.get('parameters', {})
                    await self.handle_admin_action(command, parameters)

                elif action == 'get_status':
                    # Anyone can request status
                    await self.handle_status_request()

                else:
                    logger.warning(f"Unknown action received: {action}")
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'error': f'Unknown action: {action}'
                    }))
            else:
                logger.warning(f"Received data without action from user {self.user.username}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': 'No action specified'
                }))

        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Internal server error'
            }))

    async def send_data(self, event):
        """
        Send data to the WebSocket client.

        This method is called when data is broadcast to the WebSocket group.
        It filters the data based on the user's role before sending.

        Args:
            event: The event containing the data to send
        """
        try:
            data = event.get('data', {})

            # Filter data based on user role if needed
            filtered_data = await self.filter_data_by_role(data)

            # Send data to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'data',
                'data': filtered_data
            }))

        except Exception as e:
            logger.error(f"Error sending data to WebSocket: {str(e)}")
            # Don't raise the exception to avoid breaking the WebSocket connection

    async def handle_status_request(self):
        """Handle a request for system status information."""
        try:
            # Import here to avoid circular imports
            from .msr_protocol import connection_state, connection_settings, calibration_settings

            # Create a status response with appropriate information for the user's role
            status_data = {
                'type': 'status',
                'timestamp': asyncio.get_event_loop().time(),
                'connection': {
                    'connected': connection_state['connected'],
                    'last_connected': connection_state['last_connected']
                }
            }

            # Add role-specific information
            if self.user_role in ['calibrator', 'admin']:
                status_data['calibration'] = calibration_settings
                status_data['connection']['reconnect_attempts'] = connection_state['reconnect_attempts']

            if self.user_role == 'admin':
                status_data['connection']['settings'] = connection_settings
                status_data['connection']['last_error'] = connection_state['last_error']

            # Send the status response
            await self.send(text_data=json.dumps(status_data))

        except Exception as e:
            logger.error(f"Error handling status request: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Failed to retrieve status information'
            }))

    @database_sync_to_async
    def get_user_role(self):
        """
        Get the role of the current user.

        Returns:
            str: The user's role (operator, calibrator, or admin)
        """
        try:
            return self.user.role.role
        except Exception as e:
            logger.warning(f"Failed to get role for user {self.user.username}: {str(e)}")
            return 'operator'  # Default role

    @database_sync_to_async
    def filter_data_by_role(self, data):
        """
        Filter data based on the user's role.

        This method removes sensitive or role-specific data from the response
        based on the user's permission level.

        Args:
            data: The data to filter

        Returns:
            dict: The filtered data appropriate for the user's role
        """
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

    async def handle_calibration(self, parameters):
        """Handle calibration requests from calibrators and admins"""
        from msr_control.msr_protocol import update_calibration

        try:
            # Update calibration settings
            updated_settings = await update_calibration(parameters)

            # Send confirmation back to the client
            await self.send(text_data=json.dumps({
                'success': True,
                'message': 'Calibration settings updated successfully',
                'settings': updated_settings
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to update calibration settings: {str(e)}'
            }))

    async def handle_admin_action(self, command, parameters):
        """Handle admin actions"""
        if command == 'update_settings':
            await self.update_connection_settings(parameters)
        elif command == 'restart_service':
            await self.restart_service()
        elif command == 'add_user':
            await self.add_user(parameters)
        else:
            await self.send(text_data=json.dumps({
                'error': f'Unknown admin command: {command}'
            }))

    async def update_connection_settings(self, parameters):
        """Update connection settings"""
        from msr_control.msr_protocol import update_connection_settings

        try:
            # Update connection settings
            updated_settings = await update_connection_settings(parameters)

            # Send confirmation back to the client
            await self.send(text_data=json.dumps({
                'success': True,
                'message': 'Connection settings updated successfully',
                'settings': updated_settings
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Failed to update connection settings: {str(e)}'
            }))

    async def restart_service(self):
        """Restart the service (simulated)"""
        # In a real application, you would implement actual service restart logic
        await self.send(text_data=json.dumps({
            'success': True,
            'message': 'Service restart initiated. This may take a few moments.'
        }))

        # Simulate a restart by waiting a bit
        await asyncio.sleep(2)

        await self.send(text_data=json.dumps({
            'success': True,
            'message': 'Service restarted successfully.'
        }))

    @database_sync_to_async
    def add_user(self, parameters):
        """Add a new user to the system"""
        from django.contrib.auth.models import User
        from msr_control.models import UserRole

        try:
            username = parameters.get('username')
            password = parameters.get('password')
            role = parameters.get('role', 'operator')

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return {'success': False, 'error': 'Username already exists'}

            # Create the user
            user = User.objects.create_user(
                username=username,
                password=password
            )

            # Create the user role
            UserRole.objects.create(user=user, role=role)

            return {
                'success': True,
                'message': f'User {username} created successfully with role {role}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
