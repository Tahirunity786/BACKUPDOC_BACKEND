from django.urls import path
from core__a.views import ALLDoctorListAPIView, ChangePasswordView,CitySearchAPIView, ContactTicketListCreateView, DoctorListByCityAPIView, DoctorTimeSlotsCreate, PasswordResetConfirmView, PasswordResetRequestView, Register, SearchDoctorByCityView, UserLogin, EmailChecker, UpdateProfileView
urlpatterns = [
     path('register', Register.as_view(), name='register'),
     path('login', UserLogin.as_view(), name='login'),
     path('email-check', EmailChecker.as_view(), name='emailcheck'),
     path('user/update-profile/', UpdateProfileView.as_view(), name='updateProfile'),
     path('user/update-profile/change-password/', ChangePasswordView.as_view(), name='chngpass'),
     path('reset-request', PasswordResetRequestView.as_view(), name='requestreset'),
     path('request-confirm', PasswordResetConfirmView.as_view(), name='resetconfirm'),
     path('tickets/', ContactTicketListCreateView.as_view(), name='contact-ticket-list-create'),
     path('search-doctor/', SearchDoctorByCityView.as_view(), name='search-doctor'),
     path('cities', CitySearchAPIView.as_view(), name='search-cities'),
     path('by-city', DoctorListByCityAPIView.as_view(), name='doctor-list-by-city'),
     path('all-doctors', ALLDoctorListAPIView.as_view(), name='doctor-lis'),
     path('add-time-slots', DoctorTimeSlotsCreate.as_view(), name='time-slots-create'),
]
