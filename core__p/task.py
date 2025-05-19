import os
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from core__p.models import Patients, PatientXray

User = get_user_model()

@shared_task
def process_xray_upload(user_id, filename, file_path, patient_id=None):
    """
    Background task to process and save X-ray image for a doctor or patient.

    - For doctors: Requires a valid patient ID to associate the X-ray with a patient.
    - For patients: Directly associates the X-ray with the authenticated user.
    """

    # Ensure the file exists
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # Cleanup if user is invalid
        os.remove(file_path)
        return {"error": "Invalid user ID. Upload cancelled."}

    # Handle doctor user type
    if user.user_type == 'doctor':
        if not patient_id:
            os.remove(file_path)
            return {"error": "Patient ID is required for doctor uploads."}
        try:
            patient = Patients.objects.get(_id=patient_id)
        except Patients.DoesNotExist:
            os.remove(file_path)
            return {"error": "Patient not found."}

        # Save X-ray associated with a patient (for doctor)
        relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT).replace("\\", "/")
        xray_object = PatientXray.objects.create(
            image=relative_path
        )
        patient.patient_xrays.add(xray_object)
        patient.save()
        return {"message": "X-ray uploaded successfully for patient."}

    # Handle patient user type (no Patients object required)
    elif user.user_type == 'patient':
        relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT).replace("\\", "/")
        PatientXray.objects.create(
            user=user,
            image=relative_path
        )
        return {"message": "X-ray uploaded successfully for user."}

    else:
        os.remove(file_path)
        return {"error": "Unsupported user type."}
