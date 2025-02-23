from django.shortcuts import render
from langchain_demos.constraint_gen import LaTeXGenerator
import cv2
from django.http import HttpResponse, FileResponse, JsonResponse
import os
import subprocess
import re
from .forms import DocumentForm
from .models import Document
import base64

from django.shortcuts import render, redirect, get_object_or_404
from .models import Document
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets, permissions, status
from .models import Document
from .serializers import DocumentSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging
from django.views.decorators.csrf import csrf_exempt
from autopres import PresentationGenerator

from django.shortcuts import render
from django.http import JsonResponse
import torch

import tempfile
import os
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import numpy as np
import speech_recognition as sr
from django.shortcuts import render
from django.http import StreamingHttpResponse

# import whisper


def section_display(request):
    sections = [
        {
            "title": "Introduction and Problem Statement",
            "text": "Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.",
            "suggestions": "This section could benefit from a more concise introduction that directly states the problem before diving into examples.",
            "image_suggestions": "robot performing complex task, robot manipulation in kitchen, long horizon task planning robot",
        },
        {
            "title": "Current Methods and Limitations",
            "text": "Current methods to solve these long horizon tasks fall largely into two campaigns...",
            "suggestions": "This section would benefit from clearer explanations of 'task and motion planning' and 'behavioral tasks/RL'.",
            "image_suggestions": "task and motion planning diagram, reinforcement learning robot diagram, visual language model robot interaction",
        },
        {
            "title": "Proposed Approach and Emphasis",
            "text": "This raises an employee to perform long-horizon tasks and real- the semantics of natural language instruction...",
            "suggestions": "This section is very unclear and needs significant improvement.",
            "image_suggestions": "Natural Language Robot Instruction, Robot low-level skills, generalizable measure of robot task performance",
        },
        {
            "title": "New",
            "text": "Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.",
            "suggestions": "This section could benefit from a more concise introduction that directly states the problem before diving into examples.",
            "image_suggestions": "robot performing complex task, robot manipulation in kitchen, long horizon task planning robot",
        },
        {
            "title": "New2",
            "text": "Current methods to solve these long horizon tasks fall largely into two campaigns...",
            "suggestions": "This section would benefit from clearer explanations of 'task and motion planning' and 'behavioral tasks/RL'.",
            "image_suggestions": "task and motion planning diagram, reinforcement learning robot diagram, visual language model robot interaction",
        },
        {
            "title": "New3",
            "text": "This raises an employee to perform long-horizon tasks and real- the semantics of natural language instruction...",
            "suggestions": "This section is very unclear and needs significant improvement.",
            "image_suggestions": "Natural Language Robot Instruction, Robot low-level skills, generalizable measure of robot task performance",
        },
        {
            "title": "New4",
            "text": "Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.Second latency. With robots becoming increasingly prominent in society, so too does the desire for them to solve complex multistage tasks increase.",
            "suggestions": "This section could benefit from a more concise introduction that directly states the problem before diving into examples.",
            "image_suggestions": "robot performing complex task, robot manipulation in kitchen, long horizon task planning robot",
        },
        {
            "title": "New5",
            "text": "Current methods to solve these long horizon tasks fall largely into two campaigns...",
            "suggestions": "This section would benefit from clearer explanations of 'task and motion planning' and 'behavioral tasks/RL'.",
            "image_suggestions": "task and motion planning diagram, reinforcement learning robot diagram, visual language model robot interaction",
        },
        {
            "title": "New6",
            "text": "This raises an employee to perform long-horizon tasks and real- the semantics of natural language instruction...",
            "suggestions": "This section is very unclear and needs significant improvement.",
            "image_suggestions": "Natural Language Robot Instruction, Robot low-level skills, generalizable measure of robot task performance",
        },
    ]
    return render(request, "app/document_feedback.html", {"sections": sections})


# Load the Whisper model (choose small, medium, or large based on available resources)
# model = whisper.load_model("small")


@login_required
def document_list(request):
    documents = Document.objects.filter(owner=request.user)
    return render(request, "app/document_list.html", {"documents": documents})


logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Optionally restricts the returned documents to the owner,
        by filtering against the authenticated user.
        """
        user = self.request.user
        return Document.objects.filter(owner=user).order_by("-created_at")

    def perform_create(self, serializer):
        """
        Associates the document with the authenticated user.
        """
        print(self.request.data)
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["post"], url_path="save_document")
    def save_document(self, request):
        """
        Custom action to handle saving a document with image upload.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response({"success": True, "document_id": serializer.instance.id})
        else:
            return Response({"success": False, "errors": serializer.errors}, status=400)

    @action(detail=True, methods=["patch"], url_path="update-state")
    def update_state(self, request, pk=None):
        """
        Custom action to update document state with new text content and generate presentation
        """
        try:
            document = self.get_object()
            logger.debug(f"Updating state for document {pk}")
            logger.debug(f"Request data: {request.data}")

            if "txt_content" in request.data:
                document.txt_field = request.data["txt_content"]

                # Generate presentation from text content
                generator = PresentationGenerator()
                result = generator.generate(document.txt_field)
                document.presentation_html = result["html"]

                document.save()
                logger.debug(f"Successfully updated document {pk}")
                return Response(
                    {
                        "success": True,
                        "message": "State updated successfully",
                        "presentation_html": document.presentation_html,
                    }
                )
            else:
                logger.warning(f"No text content provided for document {pk}")
                return Response(
                    {"success": False, "error": "No text content provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            logger.error(f"Error updating document {pk}: {str(e)}")
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@login_required
def document_detail(request, document_id):
    """
    Display a specific document based on its ID.

    Args:
        request (HttpRequest): The HTTP request object.
        document_id (int): The ID of the document to display.

    Returns:
        HttpResponse: Renders the document_form.html template with the document context.
    """
    # Retrieve the document ensuring it belongs to the logged-in user
    document = get_object_or_404(Document, id=document_id, owner=request.user)

    # Render the template with the document context
    return render(request, "app/document_form.html", {"document": document})



def recompile_latex(request):
    if request.method == "POST":
        latex = request.POST["latex"]
        with open("static/output.tex", "w") as f:
            f.write(latex)

        try:
            subprocess.run(
                ["pdflatex", "-output-directory=static", "static/output.tex"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            pdf_path = "static/output.pdf"

            # Check if the PDF was created successfully
            if os.path.exists(pdf_path):
                # Return both PDF and latex content in JSON response
                with open(pdf_path, "rb") as pdf_file:
                    pdf_content = pdf_file.read()
                    pdf_base64 = base64.b64encode(pdf_content).decode("utf-8")

                return JsonResponse({"pdf": pdf_base64, "latex": latex})
            else:
                return JsonResponse({"error": "PDF compilation failed"}, status=500)

        except subprocess.CalledProcessError as e:
            return JsonResponse(
                {"error": f"Compilation error: {e.stderr.decode()}"}, status=500
            )

    return JsonResponse({"error": "Invalid request method."}, status=405)


def landing(request):
    return render(request, "frontend/landing.html")


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Document


@csrf_exempt
def save_text(request, doc_id):
    if request.method == "POST":
        document = Document.objects.get(id=doc_id)
        text_content = request.POST.get("txt_content", "")
        document.txt_field = text_content
        document.save()
        return JsonResponse({"message": "Saved successfully!"})
    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def render_presentation(request, doc_id):
    if request.method == "POST":
        document = Document.objects.get(id=doc_id)
        text_content = request.POST.get("txt_content", "")

        # Generate presentation from text content
        generator = PresentationGenerator()
        result = generator.generate(text_content)
        document.presentation_html = result["html"]
        document.save()

        return JsonResponse(
            {
                "message": "Rendered successfully!",
                "presentation_html": document.presentation_html,
            }
        )
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def presentation_view(request, document_id):
    document = get_object_or_404(Document, id=document_id, owner=request.user)
    return render(request, "app/presentation.html", {"document": document})
