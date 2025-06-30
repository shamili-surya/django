# accounts/urls.py

from django.urls import path
from .views import student_api

urlpatterns = [
     path('students/', student_api),
]
