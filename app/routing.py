# app/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"^ws/transcribe/(?P<doc_id>\d+)/$", consumers.TranscriptionConsumer.as_asgi()
    ),
]
