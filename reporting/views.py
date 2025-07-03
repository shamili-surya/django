from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from login.models import ActivityLog  # adjust if your model is elsewhere

@api_view(['GET'])
def generate_user_report_pdf(request, username):
    logs = ActivityLog.objects.filter(user__username=username).order_by('-timestamp')

    if not logs.exists():
        return Response({"message": "No logs found for this user"}, status=404)

    template = get_template("report_template.html")
    context = {
        'title': 'User Activity Report',
        'username': username,
        'logs': logs
    }
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{username}_report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return Response({"message": "PDF generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
