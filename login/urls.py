from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    register_user,
    login_user,
    list_users,
    forgot_password,
    reset_password,
    change_user_role,
    send_mail
)

urlpatterns = [
    # 🔐 Authentication & User Management
    path('register/', register_user),
    path('login/', login_user),
    path('users/', list_users),
    path('forgot-password/', forgot_password),
    path('reset-password/<uidb64>/<token>/', reset_password),
    path('change-role/', change_user_role),

    # 📧 Mailbox APIs
    path('send-mail/', send_mail),
    path('draft-mails/', views.draft_mails),
    path('inbox/', views.inbox),
    path('sent-mails/', views.sent_mails),
    path('starred-mails/', views.starred_mails),
    path('toggle-star/<int:mail_id>/', views.toggle_star),
    path('mark-as-read/<int:mail_id>/', views.mark_as_read),
    path('delete-mail/<int:mail_id>/', views.delete_mail),
    path('trash-mails/', views.trash_mails),

    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # login
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # refresh token
]
