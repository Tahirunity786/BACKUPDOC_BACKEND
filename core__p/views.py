import os
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status, generics
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from core__p.models import Appointments, Patients, PatientXray, User
from core__p.pagination import CustomPagination  # Assuming you have this
import os
from django.conf import settings
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from core__p.models import Patients
from core__p.pagination import CustomPagination
from core__p.task import process_xray_upload
from core__p.serializer import AppointmentFeedbackSerializer, AppointmentSerializer, PatientSerializer, PatientXraySerializer
from rest_framework.exceptions import NotFound
from django.core.mail import send_mail

from core__a.models import DoctorTimeSlots




class UploadImagesView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    pagination_class = CustomPagination

    def post(self, request):
        user = request.user
        files = request.FILES.getlist('files')
        patient_id = request.data.get('patient_id')

        if not files:
            return Response({"error": "No files uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        if user.user_type == 'doctor':
            if not patient_id:
                return Response({"error": "Patient ID is required for doctors."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                patient = Patients.objects.get(_id=patient_id)
            except ObjectDoesNotExist:
                return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)
            except MultipleObjectsReturned:
                return Response({"error": "Multiple patients found."}, status=status.HTTP_400_BAD_REQUEST)

        created_xrays = []

        for file in files:
            # Save temporarily
            temp_path = default_storage.save(f'temp_uploads/{file.name}', file)
            full_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, temp_path))  # Ensure it's a clean path

            # Ensure only passing the correct arguments (no full drive letters like 'D:' as filename!)
            if user.user_type == 'doctor':
                process_xray_upload.delay(user.id, os.path.basename(file.name), full_path, str(patient_id))
            elif user.user_type == 'patient':
                process_xray_upload.delay(user.id, os.path.basename(file.name), full_path)
            else:
                return Response({"error": "Unauthorized user type."}, status=status.HTTP_403_FORBIDDEN)

            created_xrays.append(file.name)

        return Response({
            "message": "Files uploaded and sent for processing.",
            "files": created_xrays
        }, status=status.HTTP_201_CREATED)

class PatientXrayListView(generics.ListAPIView):
    serializer_class = PatientXraySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'doctor':
            patient_id = self.request.query_params.get('patient_id')
            if not patient_id:
                raise NotFound("Patient ID is required.")

            try:
                patient = Patients.objects.get(_id=patient_id, doctor=user)
            except Patients.DoesNotExist:
                raise NotFound("Patient not found.")

            return patient.patient_xrays.all().order_by('-created_at')

        elif user.user_type == 'patient':
            return PatientXray.objects.filter(user=user).order_by('-created_at')

        return PatientXray.objects.none()
        
class PatientListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to list and create patients.
    - Only authenticated users can access.
    - Only users with user_type='doctor' can list and create patients.
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "doctor":
            return Patients.objects.filter(doctor=user)
        return Patients.objects.none()  # Block access to non-doctors

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type != "doctor":
            raise PermissionDenied("Only doctors are allowed to create patients.")
        serializer.save(doctor=user)


class PatientRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = '_id'

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "doctor":
            return Patients.objects.filter(doctor=user)
        return Patients.objects.none()
    
class SearchPatientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if query:
            patients = Patients.objects.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query),
                doctor=request.user
            )
        else:
            patients = Patients.objects.filter(doctor=request.user)

        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AppointmentCreateView(generics.CreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        slot_id = self.request.data.get('slot')
        appointment_date = self.request.data.get('date')

        if not slot_id or not appointment_date:
            print("I'm here")
            raise ValidationError("Slot and date are required.")

        try:
            # Optimize DB query using select_related
            slot = DoctorTimeSlots.objects.select_related('doctor').get(id=slot_id)
        except DoctorTimeSlots.DoesNotExist:
            print("I'm here 2")
            raise ValidationError("Selected slot does not exist.")

        # Check if slot is already booked
        if slot.is_booked:
            print("I'm here 3")
            raise ValidationError("This time slot is already booked.")

        # Check daily appointment limit
        if Appointments.objects.filter(patient=user, date=appointment_date).count() >= 4:
            print("I'm here 4")
            raise ValidationError("You can only book up to 4 appointments per day.")

        # Mark slot as booked
        slot.is_booked = True
        slot.save(update_fields=['is_booked'])

        # Save appointment
        appointment = serializer.save(
            patient=user,
            doctor=slot.doctor,
            full_name=f"{user.first_name} {user.last_name}",
            email=user.email,
            slot=slot,
            status='pending',
        )

        # Send email to doctor
        send_mail(
            subject="New Appointment Request",
            message=(
                f"Dear Dr. {slot.doctor.first_name},\n\n"
                f"You have a new appointment request from {user.first_name} {user.last_name}"
                f"on {appointment.date} at {slot.start_time}.\n\n"
                "Please log in to your account to manage this request.\n\n"
                "Regards,\nBackupDoc Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[slot.doctor.email],
            fail_silently=True,
        )

        
# LIST Appointments by Patient
class AppointmentListByPatientView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            user = User.objects.get(id = self.request.user.id)
        except User.DoesNotExist:
            return Response({"error":"User not found"})
        if user.user_type == 'patient':
            return Appointments.objects.filter(patient=self.request.user).order_by('-date', 'slot__start_time')
        elif user.user_type == 'doctor':
            return Appointments.objects.filter(doctor=self.request.user).order_by('-date', 'slot__start_time')
        return Appointments.objects.none()


class AppointmentUpdateView(generics.UpdateAPIView):
    """
    Allows doctors to update the status and/or slot of an appointment.
    Sends email notifications to the patient upon status change.
    """
    queryset = Appointments.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        user = self.request.user

        # ✅ Ensure only doctors can perform updates
        if not hasattr(user, 'user_type') or user.user_type.lower() != 'doctor':
            raise PermissionDenied("Only doctors can update appointments.")

        instance = self.get_object()
        prev_status = instance.status
        new_status = serializer.validated_data.get('status', prev_status)
        new_slot = serializer.validated_data.get('slot', instance.slot)

        # ✅ Handle slot change logic
        if new_slot != instance.slot:
            if new_slot.is_booked:
                raise serializers.ValidationError("This slot is already booked.")

            # Free the previous slot
            instance.slot.is_booked = False
            instance.slot.save(update_fields=['is_booked'])

            # Book the new slot
            new_slot.is_booked = True
            new_slot.save(update_fields=['is_booked'])

        # ✅ Process status transitions with email notifications
        self.handle_status_change(instance, prev_status, new_status, user)

        # ✅ Save updated instance
        serializer.save(slot=new_slot, status=instance.status)

    def handle_status_change(self, instance, prev_status, new_status, doctor):
        """
        Handles logic for appointment status transitions and email notifications.
        """
        patient = instance.patient
        appointment_time = instance.slot.start_time.strftime('%I:%M %p')
        appointment_date = instance.date

        def send_notification(subject, message):
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [patient.email])

        # Status: Approved
        if new_status.lower() == 'approved' and prev_status.lower() != 'approved':
            subject = "Your Appointment Has Been Approved"
            message = (
                f"Dear {patient.first_name},\n\n"
                f"Your appointment with Dr. {doctor.first_name} {doctor.last_name} on {appointment_date} "
                f"at {appointment_time} has been approved.\n\n"
                f"Thank you for choosing our services. We wish you good health and well-being.\n\n"
                f"Best regards,\nThe BackupDoc Team"
            )
            send_notification(subject, message)
            instance.status = 'approved'

        # Status: Declined
        elif new_status.lower() == 'declined' and prev_status.lower() != 'declined':
            subject = "Your Appointment Has Been Declined"
            message = (
                f"Dear {patient.first_name},\n\n"
                f"Sorry, but your appointment with Dr. {doctor.first_name} {doctor.last_name} on {appointment_date} "
                f"at {appointment_time} has been declined.\n\n"
                f"For more details, please contact our customer support.\n\n"
                f"Best regards,\nThe BackupDoc Team"
            )
            send_notification(subject, message)
            instance.status = 'declined'

        # Status: Resolved
        elif new_status.lower() == 'resolved' and prev_status.lower() != 'resolved':
            # Free up the current slot
            instance.slot.is_booked = False
            instance.slot.save(update_fields=['is_booked'])

            subject = "Your Appointment Has Been Completed"
            message = (
                f"Dear {patient.first_name} {patient.last_name}n\n"
                f"Your appointment with Dr. {doctor.first_name} {doctor.last_name} on {appointment_date} "
                f"at {appointment_time} has been marked as resolved.\n\n"
                f"Thank you for choosing our services. We wish you good health and well-being.\n\n"
                f"Best regards,\nThe BackupDoc Team"
            )
            send_notification(subject, message)
            instance.status = 'resolved'

class CreateAppointmentFeedbackView(generics.CreateAPIView):
    serializer_class = AppointmentFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        feedback = serializer.save(rated_by=self.request.user)

        # Access the related doctor
        doctor = feedback.appointment.doctor

        if doctor and doctor.email:
            subject = "New Appointment Feedback Received"
            message = (
                f"Hello Dr. {doctor.first_name},\n\n"
                f"You have received a new feedback from {self.request.user.first_name} {self.request.user.last_name}"
                f"for the appointment dated {feedback.appointment.date}.\n\n"
                f"Rating: {feedback.rating} stars\n"
                f"Description: {feedback.description}\n\n"
                f"Please log in to your dashboard to view more details.\n\n"
                f"Best regards,\nBackupdoc"
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [doctor.email],
                fail_silently=False
            )