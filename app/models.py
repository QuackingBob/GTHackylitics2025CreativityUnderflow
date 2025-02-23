from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    title = models.CharField(max_length=200)
    txt_content = models.FileField(
        upload_to="media/txt/", blank=True, null=True
    )  # Store in MEDIA_ROOT/txt/
    txt_field = models.TextField(blank=True, null=True)
    presentation_html = models.TextField(
        blank=True, null=True
    )  # Store the reveal.js presentation HTML
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
