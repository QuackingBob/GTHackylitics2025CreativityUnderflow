from rest_framework import serializers
from .models import Document

from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    txt_content = serializers.FileField(required=False, allow_null=True)
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Document
        fields = ['id', 'title', 'txt_field', 'txt_content', 'created_at', 'owner']
        read_only_fields = ['created_at']