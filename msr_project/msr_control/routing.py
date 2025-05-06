from django.urls import path
from msr_control import consumers

websocket_urlpatterns = [
    path('ws/msr_data/', consumers.MSRConsumer.as_asgi()),
]
