from django.urls import path
from .views import generate_user_report_pdf

urlpatterns = [
    path('generate-user-report-pdf/<str:username>/', generate_user_report_pdf),
]
