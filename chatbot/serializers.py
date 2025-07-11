from rest_framework import serializers
from .models import UploadedPDF

class UploadedPDFSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedPDF
        fields = ['id', 'title', 'pdf_file', 'uploaded_at']
