from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError

from .models import Patients, PatientXray
from .serializers import PatientXraySerializer
from .pagination import CustomPagination
from .tasks import process_xray_upload  # Celery task

class UploadImagesView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    pagination_class = CustomPagination

    def post(self, request):
        user = request.user
        files = request.FILES.getlist('files')
        patient_id = request.data.get('patient_id')

        # Ensure files are uploaded
        if not files:
            return Response({"error": "No files uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        created_xrays = []

        # Doctor: Save under a patient
        if user.user_type == 'doctor':
            if not patient_id:
                return Response({"error": "Patient ID is required for doctors."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                patient = Patients.objects.get(_id=patient_id)
            except ObjectDoesNotExist:
                return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)
            except MultipleObjectsReturned:
                return Response({"error": "Multiple patients found."}, status=status.HTTP_400_BAD_REQUEST)

            # Queue Celery task for each image
            for file in files:
                task = process_xray_upload.delay(user.id, file.name, file.read(), patient_id)
                created_xrays.append(file.name)

        # Patient: Upload directly (no patient object linkage)
        elif user.user_type == 'patient':
            for file in files:
                task = process_xray_upload.delay(user.id, file.name, file.read())
                created_xrays.append(file.name)

        else:
            return Response({"error": "Unauthorized user type."}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "message": "X-ray upload tasks submitted successfully.",
            "files": created_xrays
        }, status=status.HTTP_202_ACCEPTED)
