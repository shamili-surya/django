from django.urls import path
from .views import (
    register_user,
    login_user,
    list_users,
    forgot_password,
    reset_password,
    change_user_role  # ✅ New import
)

urlpatterns = [
    path('register/', register_user),
    path('login/', login_user),
    path('users/', list_users),

    # ✅ Forgot & Reset Password URLs
    path('forgot-password/', forgot_password),
    path('reset-password/<uidb64>/<token>/', reset_password),

    # ✅ Change Role API
    path('change-role/', change_user_role),  # 💥 Added new API route
]
