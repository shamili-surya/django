from django.shortcuts import render

# Create your views here.
# accounts/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Student  
from .serializers import StudentSerializer

@api_view(['GET', 'POST'])
def student_api(request):
    if request.method == 'GET':
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Data created successfully', 'data': serializer.data})
        return Response(serializer.errors)
