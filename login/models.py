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

class Mail(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_mails')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_draft = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

class MailRecipient(models.Model):
    RECIPIENT_TYPE_CHOICES = (
        ('to', 'To'),
        ('cc', 'CC'),
        ('bcc', 'BCC'),
    )

    mail = models.ForeignKey(Mail, on_delete=models.CASCADE, related_name='recipients')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipient_type = models.CharField(max_length=3, choices=RECIPIENT_TYPE_CHOICES)
    is_starred = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

