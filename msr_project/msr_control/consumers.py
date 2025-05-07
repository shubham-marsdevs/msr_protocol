import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class MSRConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "msr_data"
        self.room_group_name = f"msr_{self.room_name}"
        self.user = self.scope["user"]

        # Check if user is authenticated
        if self.user == AnonymousUser():
            # Reject the connection if user is not authenticated
            await self.close()
            return

        # Get user role
        self.user_role = await self.get_user_role()

        # Join the WebSocket group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the WebSocket group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming messages from WebSocket (if needed)
        try:
            data = json.loads(text_data)
            # Process based on user role
            if 'action' in data:
                action = data['action']

                # Check permissions based on role
                if action == 'calibrate' and not (self.user_role in ['calibrator', 'admin']):
                    await self.send(text_data=json.dumps({
                        'error': 'Permission denied. Calibration requires Calibrator or Admin role.'
                    }))
                    return

                if action == 'admin_action' and self.user_role != 'admin':
                    await self.send(text_data=json.dumps({
                        'error': 'Permission denied. This action requires Admin role.'
                    }))
                    return

                # Process the action based on the type
                if action == 'calibrate':
                    await self.handle_calibration(data.get('parameters', {}))
                elif action == 'admin_action':
                    command = data.get('command', '')
                    parameters = data.get('parameters', {})
                    await self.handle_admin_action(command, parameters)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))

    async def send_data(self, event):
        data = event.get('data', {})

        # Filter data based on user role if needed
        filtered_data = await self.filter_data_by_role(data)

        # Send data to WebSocket
        await self.send(text_data=json.dumps({
            'data': filtered_data
        }))

    @database_sync_to_async
    def get_user_role(self):
        try:
            return self.user.role.role
        except:
            return 'operator'  # Default role

    @database_sync_to_async
    def filter_data_by_role(self, data):
        # Example of filtering data based on user role
        # This can be customized based on your specific requirements
        if isinstance(data, dict):
            if self.user_role == 'operator':
                # Operators only see basic data
                return {k: v for k, v in data.items() if k not in ['admin_data', 'calibration_data']}
            elif self.user_role == 'calibrator':
                # Calibrators see everything except admin data
                return {k: v for k, v in data.items() if k != 'admin_data'}
            else:  # Admin sees everything
                return data
        return data

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
