from django.urls import path
from core__p.views import *

urlpatterns = [
    path('upload/', UploadImagesView.as_view(), name="upload-images"),
    path('images/', PatientXrayListView.as_view(), name="uploaded-images"),
    path('patients/', PatientListCreateAPIView.as_view(), name='patient-list-create'),
    path('patients/<str:_id>/', PatientRetrieveUpdateDestroyAPIView.as_view(), name='patient-detail'),
    path('search', SearchPatientsView.as_view(), name='search-patients'),
    path('appointments/create/', AppointmentCreateView.as_view(), name='appointment-create'),
    path('appointments/list/', AppointmentListByPatientView.as_view(), name='appointment-list'),
    path('appointments/update/<int:id>/', AppointmentUpdateView.as_view(), name='appointment-update'),
    path('feedback/', CreateAppointmentFeedbackView.as_view(), name='appointment-feedback'),
]