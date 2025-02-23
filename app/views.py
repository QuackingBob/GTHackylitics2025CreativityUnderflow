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
import io
import numpy as np
import torch
import whisper
import resampy
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
from queue import Queue
from pydub import AudioSegment
from torch.nn.attention import SDPBackend, sdpa_kernel
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

logger = logging.getLogger(__name__)

# Replace lines 40-44 with:
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "openai/whisper-large-v3"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True,
    use_flash_attention_2=True,
).to(device)

# Remove compilation and just use static cache
model.config.use_cache = True
model.generation_config.max_new_tokens = 256

processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)

audio_queue = Queue()


@csrf_exempt
def process_audio(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    audio_file = request.FILES.get("audio")
    if not audio_file:
        return JsonResponse({"error": "No audio file provided"}, status=400)

    try:
        # First try direct WEBM decoding
        audio_bytes = audio_file.read()
        try:
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_bytes), format="webm"
            )
        except Exception as e:
            logger.warning(f"Direct WEBM decoding failed: {e}, trying with ffmpeg")
            # If direct decoding fails, try with explicit ffmpeg parameters
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_bytes),
                format="webm",
                codec="opus",
                parameters=["-strict", "-2"],
            )

        # Convert to mono and 16kHz sample rate
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_frame_rate(16000)

        # Export as raw PCM
        audio_data = np.array(
            audio_segment.get_array_of_samples(), dtype=np.float32
        ) / (2**15)

        audio_queue.put(audio_data)
        logger.debug(f"Current audio queue size: {audio_queue.qsize()}")
        return JsonResponse({"status": "audio received"})

    except Exception as e:
        logger.exception("Error processing audio")
        return JsonResponse(
            {
                "error": f"Audio processing failed: {str(e)}. Make sure ffmpeg is installed with webm/opus support."
            },
            status=500,
        )


def generate_transcription():
    global pipe
    try:
        while True:
            audio_data = audio_queue.get()
            if audio_data is None:  # Signal to stop
                break

            # Remove sdpa_kernel context manager and simplify
            result = pipe({"array": audio_data, "sampling_rate": 16000})
            text = result["text"].strip()

            if text:
                yield f"data: {text}\n\n"

    except Exception as e:
        logger.exception("Error in generate_transcription")
        yield f"data: Error: {str(e)}\n\n"


def start_transcription(request):
    return StreamingHttpResponse(
        generate_transcription(), content_type="text/event-stream"
    )


def document_speak(request):
    return render(request, "app/document_speak.html")


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
        Custom action to update document state with new text content
        """
        try:
            document = self.get_object()
            logger.debug(f"Updating state for document {pk}")
            logger.debug(f"Request data: {request.data}")
            logger.debug(f"Request headers: {request.headers}")

            if "txt_content" in request.data:
                document.txt_field = request.data["txt_content"]
                document.save()
                logger.debug(f"Successfully updated document {pk}")
                return Response(
                    {"success": True, "message": "State updated successfully"}
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


def document_list(request):
    documents = Document.objects.filter(owner=request.user)

    return render(request, "app/document_list.html", {"documents": documents})


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
        try:
            document = get_object_or_404(Document, id=doc_id)
            text_content = request.POST.get("txt_content", "")

            if not text_content:
                return JsonResponse({"error": "No text content provided"}, status=400)

            # Generate presentation from text content
            generator = PresentationGenerator()
            try:
                result = generator.generate(text_content)
                document.presentation_html = result["html"]
                document.save()

                return JsonResponse(
                    {
                        "message": "Rendered successfully!",
                        "presentation_html": document.presentation_html,
                    }
                )
            except Exception as e:
                logger.error(f"Presentation generation error: {str(e)}")
                return JsonResponse(
                    {"error": f"Failed to generate presentation: {str(e)}"}, status=500
                )

        except Document.DoesNotExist:
            return JsonResponse({"error": "Document not found"}, status=404)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({"error": "Server error"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required
def presentation_view(request, document_id):
    document = get_object_or_404(Document, id=document_id, owner=request.user)
    return render(request, "app/presentation.html", {"document": document})
