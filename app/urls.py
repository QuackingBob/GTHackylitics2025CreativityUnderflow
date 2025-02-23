"""AakashK URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"documents", views.DocumentViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("save_text/<int:doc_id>/", views.save_text, name="save_text"),
    path("documents/", views.document_list, name="document_list"),
    path("", views.landing, name="document_list"),
    path("documents/<int:document_id>/", views.document_detail, name="document_detail"),
    path("documents/speak/", views.document_speak, name="document_speak"),
    path("transcribe/", views.start_transcription, name="transcribe"),
    path(
        "render_presentation/<int:doc_id>/",
        views.render_presentation,
        name="render_presentation",
    ),
    path(
        "documents/<int:document_id>/present/",
        views.presentation_view,
        name="presentation_view",
    ),
        path('process_audio/', views.process_audio, name='process_audio'),
    path('transcribe/', views.start_transcription, name='start_transcription'),
    path('speak/', views.document_speak, name='document_speak'),
    path("documents/sections/<int:doc_id>/", views.section_display, name="section_display"),
    path("sections/<int:doc_id>/", views.update_script, name="sections"),
]
