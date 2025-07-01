from django.conf import settings
from django.db import models

class PasswordHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)


from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
