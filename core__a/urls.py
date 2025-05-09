from django.urls import path
from core__a.views import ChangePasswordView, ContactTicketListCreateView, PasswordResetConfirmView, PasswordResetRequestView, Register, UserLogin, EmailChecker, UpdateTuteeProfileView
urlpatterns = [
     path('register', Register.as_view(), name='register'),
     path('login', UserLogin.as_view(), name='login'),
     path('email-check', EmailChecker.as_view(), name='emailcheck'),
     path('user/update-profile/<str:user_type>/', UpdateTuteeProfileView.as_view(), name='updateProfile'),
     path('user/update-profile/change-password/', ChangePasswordView.as_view(), name='chngpass'),
     path('reset-request', PasswordResetRequestView.as_view(), name='requestreset'),
     path('request-confirm', PasswordResetConfirmView.as_view(), name='resetconfirm'),
     path('tickets/', ContactTicketListCreateView.as_view(), name='contact-ticket-list-create'),


]
