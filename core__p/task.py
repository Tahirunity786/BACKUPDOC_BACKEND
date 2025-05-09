from celery import shared_task
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from .models import Patients, PatientXray

User = get_user_model()

@shared_task
def process_xray_upload(user_id, filename, file_data, patient_id=None):
    """
    Background task to create and save PatientXray objects.
    For doctors, links the x-ray to a patient.
    For patients, saves independently.
    """
    try:
        user = User.objects.get(id=user_id)
        image = ContentFile(file_data, name=filename)

        # Create X-ray object
        xray = PatientXray.objects.create(user=user, image=image, is_annovated=False)

        # If doctor and patient provided, associate x-ray with patient
        if patient_id:
            try:
                patient = Patients.objects.get(_id=patient_id)
                patient.patient_xrays.add(xray)
                patient.save()
            except Patients.DoesNotExist:
                # Optional: log or notify failure to associate patient
                pass

        return True
    except Exception as e:
        # Optional: log the exception
        return False
