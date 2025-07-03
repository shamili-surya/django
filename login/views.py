from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail as django_send_mail
from django.contrib.auth.hashers import check_password

from .serializers import UserSerializer, UserGroupsSerializer
from .models import PasswordHistory, ActivityLog
from .serializers import MailSerializer  
from .models import Mail, MailRecipient  

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()
token_generator = PasswordResetTokenGenerator()

def save_password_history(user, new_password_hashed):
    PasswordHistory.objects.create(user=user, password=new_password_hashed)
    history = PasswordHistory.objects.filter(user=user).order_by('-created_at')
    if history.count() > 3:
        for old in history[3:]:
            old.delete()

def is_password_reused(user, new_password):
    previous_passwords = PasswordHistory.objects.filter(user=user)
    for entry in previous_passwords:
        if check_password(new_password, entry.password):
            return True
    return False

@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

       
        try:
            user_role = Group.objects.get(name=user.role)
        except Group.DoesNotExist:
            return Response({
                "message": f"Group '{user.role}' does not exist. Please create it.",
                "status_code": 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payload = {"customuser": user.pk, "group": user_role.pk}  
        group_serializer = UserGroupsSerializer(data=payload)
        if group_serializer.is_valid():
            group_serializer.save()
        else:
            return Response({
                "message": "Failed to assign group",
                "errors": group_serializer.errors,
                "status_code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        ActivityLog.objects.create(user=user, action='register', details="User registered")

        return Response({
            "status": 1,
            "errors": [],
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "mobile_number": user.mobile_number
            },
            "message": "User registered successfully",
            "status_code": status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED)

    return Response({
        "status": 0,
        "errors": serializer.errors,
        "message": "Validation failed",
        "status_code": status.HTTP_400_BAD_REQUEST
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        ActivityLog.objects.create(user=user, action='login', details="User logged in")

        return Response({
            'message': 'Login successful',
            'role': user.role,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_200_OK)

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def list_users(request):
    users = User.objects.all()
    data = []
    for user in users:
        role = getattr(user, 'role', 'unknown')
        data.append({
            'username': user.username,
            'email': user.email,
            'role': role
        })
    return Response(data, status=status.HTTP_200_OK)

from django.core.mail import send_mail as django_send_mail  

@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')
    if not email:
        return Response({"message": "Email is required", "status_code": 400}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"message": "User not found", "status_code": 404}, status=status.HTTP_404_NOT_FOUND)

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)
    reset_url = f"http://127.0.0.1:8000/api/reset-password/{uidb64}/{token}/"

    
    django_send_mail(
        subject='Reset Your Password',
        message=f'Click the link to reset your password:\n{reset_url}',
        from_email='no-reply@example.com',
        recipient_list=[email],
    )

    return Response({"message": "Reset link sent to email", "status_code": 200}, status=status.HTTP_200_OK)


@api_view(['POST'])
def reset_password(request, uidb64, token):
    password = request.data.get('password')
    if not password:
        return Response({"message": "Password is required", "status_code": 400}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return Response({"message": "Invalid reset link", "status_code": 400}, status=status.HTTP_400_BAD_REQUEST)

    if not token_generator.check_token(user, token):
        return Response({"message": "Token is invalid or expired", "status_code": 401}, status=status.HTTP_401_UNAUTHORIZED)

    if is_password_reused(user, password):
        return Response({"message": "You cannot reuse the last 3 passwords", "status_code": 400}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(password)
    user.save()

    save_password_history(user, user.password)
    ActivityLog.objects.create(user=user, action='password_reset', details="User reset password")

    return Response({"message": "Password reset successful", "status_code": 200}, status=status.HTTP_200_OK)

@api_view(['POST'])
def change_user_role(request):
    username = request.data.get('username')
    new_role = request.data.get('new_role')

    if not username or not new_role:
        return Response({
            "message": "Username and new_role are required",
            "status_code": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    if new_role not in ['admin', 'user']:
        return Response({
            "message": "Role must be either 'admin' or 'user'",
            "status_code": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"message": "User not found", "status_code": 404}, status=status.HTTP_404_NOT_FOUND)

    user.role = new_role
    user.save()

    user.groups.clear()

    try:
        group = Group.objects.get(name=new_role)
    except Group.DoesNotExist:
        return Response({
            "message": f"Group '{new_role}' does not exist",
            "status_code": 500
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    group_data = {"customuser": user.pk, "group": group.pk}  # <-- fixed here
    group_serializer = UserGroupsSerializer(data=group_data)
    if group_serializer.is_valid():
        group_serializer.save()
    else:
        return Response({
            "message": "Failed to assign group",
            "errors": group_serializer.errors,
            "status_code": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    ActivityLog.objects.create(
        user=user,
        action="role_change",
        details=f"Role changed to {new_role}"
    )

    return Response({
        "message": f"Role updated to '{new_role}' successfully",
        "status_code": 200,
        "user": {
            "username": user.username,
            "new_role": user.role
        }
    }, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_mail(request):
    serializer = MailSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        mail = serializer.save()

        ActivityLog.objects.create(
            user=request.user,
            action='send_mail' if not mail.is_draft else 'save_draft',
            details=f"Mail to: {request.data.get('to', [])}"
        )

        return Response({
            "message": "Mail sent successfully" if not mail.is_draft else "Draft saved successfully",
            "status_code": 201
        }, status=status.HTTP_201_CREATED)

    return Response({
        "message": "Validation error",
        "errors": serializer.errors,
        "status_code": 400
    }, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inbox(request):
    user = request.user
    recipient_entries = MailRecipient.objects.filter(user=user).select_related('mail').order_by('-mail__created_at')

    inbox_data = []
    for entry in recipient_entries:
        mail = entry.mail
        inbox_data.append({
            "mail_id": mail.id,
            "subject": mail.subject,
            "body": mail.body,
            "sender": mail.sender.username,
            "recipient_type": entry.recipient_type,
            "is_starred": entry.is_starred,
            "is_read": entry.is_read,
            "created_at": mail.created_at,
            "sent_at": mail.sent_at,
        })

    return Response({
        "message": "Inbox retrieved successfully",
        "status_code": 200,
        "inbox": inbox_data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sent_mails(request):
    user = request.user
    mails = Mail.objects.filter(sender=user, is_draft=False).order_by('-sent_at')

    sent_data = []
    for mail in mails:
        recipients = mail.recipients.all()
        sent_data.append({
            "mail_id": mail.id,
            "subject": mail.subject,
            "body": mail.body,
            "to": [r.user.email for r in recipients if r.recipient_type == 'to'],
            "cc": [r.user.email for r in recipients if r.recipient_type == 'cc'],
            "bcc": [r.user.email for r in recipients if r.recipient_type == 'bcc'],
            "created_at": mail.created_at,
            "sent_at": mail.sent_at,
        })

    return Response({
        "message": "Sent mails retrieved successfully",
        "status_code": 200,
        "sent_mails": sent_data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def draft_mails(request):
    user = request.user
    drafts = Mail.objects.filter(sender=user, is_draft=True).order_by('-created_at')

    draft_data = []
    for mail in drafts:
        recipients = mail.recipients.all()
        draft_data.append({
            "mail_id": mail.id,
            "subject": mail.subject,
            "body": mail.body,
            "to": [r.user.email for r in recipients if r.recipient_type == 'to'],
            "cc": [r.user.email for r in recipients if r.recipient_type == 'cc'],
            "bcc": [r.user.email for r in recipients if r.recipient_type == 'bcc'],
            "created_at": mail.created_at,
        })

    return Response({
        "message": "Draft mails retrieved successfully",
        "status_code": 200,
        "draft_mails": draft_data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def starred_mails(request):
    user = request.user
    starred_entries = MailRecipient.objects.filter(user=user, is_starred=True).select_related('mail').order_by('-mail__created_at')

    starred_data = []
    for entry in starred_entries:
        mail = entry.mail
        starred_data.append({
            "mail_id": mail.id,
            "subject": mail.subject,
            "body": mail.body,
            "sender": mail.sender.username,
            "recipient_type": entry.recipient_type,
            "is_starred": entry.is_starred,
            "is_read": entry.is_read,
            "created_at": mail.created_at,
            "sent_at": mail.sent_at,
        })

    return Response({
        "message": "Starred mails retrieved successfully",
        "status_code": 200,
        "starred_mails": starred_data
    }, status=status.HTTP_200_OK)

