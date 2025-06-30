from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password

from .serializers import UserSerializer, UserGroupsSerializer
from .models import UserProfile, PasswordHistory, ActivityLog

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

        profile = UserProfile.objects.get(user=user)
        profile.role = 'user'
        profile.save()

        user_role = Group.objects.get(name="user")
        payload = {"user": user.pk, "group": user_role.pk}
        group_serializer = UserGroupsSerializer(data=payload)
        if group_serializer.is_valid():
            group_serializer.save()

        ActivityLog.objects.create(user=user, action='register', details="User registered")

        return Response({
            "status": 1,
            "errors": [],
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": profile.role,
                "mobile_number": profile.mobile_number
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
        profile = UserProfile.objects.get(user=user)
        ActivityLog.objects.create(user=user, action='login', details="User logged in")
        return Response({'message': 'Login successful', 'role': profile.role}, status=status.HTTP_200_OK)

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
def list_users(request):
    users = User.objects.all()
    data = []
    for user in users:
        role = getattr(user.userprofile, 'role', 'unknown')
        data.append({
            'username': user.username,
            'email': user.email,
            'role': role
        })
    return Response(data, status=status.HTTP_200_OK)

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

    send_mail(
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
        profile = user.userprofile
    except User.DoesNotExist:
        return Response({"message": "User not found", "status_code": 404}, status=status.HTTP_404_NOT_FOUND)
    except UserProfile.DoesNotExist:
        return Response({"message": "UserProfile not found", "status_code": 404}, status=status.HTTP_404_NOT_FOUND)

    profile.role = new_role
    profile.save()

    user.groups.clear()

    try:
        group = Group.objects.get(name=new_role)
    except Group.DoesNotExist:
        return Response({
            "message": f"Group '{new_role}' does not exist",
            "status_code": 500
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    group_data = {"user": user.pk, "group": group.pk}
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
            "new_role": profile.role
        }
    }, status=status.HTTP_200_OK)
