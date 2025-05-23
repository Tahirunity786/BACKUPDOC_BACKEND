# -*- coding: utf-8 -*-
from django.utils import timezone
from datetime import timedelta
import requests as alpha_request
import os
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from celery.result import AsyncResult
from django.conf import settings
from core__p.models import PatientXray
from core__e.models import Analysis
from core__e.serializers import AnalysisSerializer
from core__p.pagination import CustomPagination
from .task import process_prediction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from django.core.mail import EmailMessage

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from django.core.mail import EmailMessage
import openai
import matplotlib.pyplot as plt


User = get_user_model()


class EngineView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            image_ids = request.data.getlist('image_ids')

            if not image_ids:
                return Response({"error": "No image IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

            images_qs = PatientXray.objects.filter(_id__in=image_ids)

            if not images_qs.exists():
                return Response({"error": "No images found for the provided IDs."}, status=status.HTTP_404_NOT_FOUND)
            process_ids = []

            for image in images_qs:
                abs_path = image.image.path
                rel_path = os.path.relpath(abs_path, settings.MEDIA_ROOT).replace("\\", "/")  # Normalize

                task = process_prediction.delay(rel_path, request.user.id)
                process_ids.append(task.id)

            return Response({
                "process_id": process_ids
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskResultView(APIView):
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        if result.ready():
            if result.successful():
                analyzed_image, output_path, analysis_id,prediction_objs = result.get()
                return Response({
                    "image_url": f'{settings.MEDIA_URL}{analyzed_image}',
                    "file_path": f'{settings.MEDIA_URL}{output_path}',
                    "analysis_id": analysis_id,
                    'prediction_objs':prediction_objs,
                    "analysis_id": analysis_id
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Task failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"status": "Processing"}, status=status.HTTP_202_ACCEPTED)
    

class AnalysisUpdateDeleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, analysis_id):
        """
        Update `is_corrected` or `report_analysis` field.
        Only the doctor who owns the analysis can update it.
        """
        analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)

        is_corrected = request.data.get('is_corrected')
        report_note = request.data.get('report_analysis')

        if is_corrected not in ['yes', 'no']:
            return Response({"detail": "Invalid value for is_corrected."}, status=status.HTTP_400_BAD_REQUEST)

        analysis.is_corrected = is_corrected
        if report_note:
            analysis.note = report_note

        analysis.save()

        return Response({"detail": "Analysis updated successfully."}, status=status.HTTP_200_OK)

    def delete(self, request, analysis_id):
        """
        Delete the analysis if it belongs to the authenticated doctor.
        """
        analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
        analysis.delete()
        return Response({"detail": "Analysis deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class UserAnalysisListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return Analysis.objects.filter(user=self.request.user).order_by('-date_time')

class FilteredAnalysisListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        filter_param = self.request.query_params.get('filter', '').lower()

        now = timezone.now()
        if filter_param == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_param == '3days':
            start_date = now - timedelta(days=3)
        elif filter_param == 'week':
            start_date = now - timedelta(weeks=1)
        elif filter_param == 'month':
            start_date = now - timedelta(days=30)
        elif filter_param == 'year':
            start_date = now - timedelta(days=365)
        else:
            # No filter or unknown filter — return all for user
            return Analysis.objects.filter(user=user).order_by('-date_time')

        return Analysis.objects.filter(user=user, date_time__gte=start_date).order_by('-date_time')

class EmailAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, analysis_id):
        try:
            analysis = Analysis.objects.get(id=analysis_id, user=request.user)

            # Determine recipient
            recipient_email = request.data.get("email", request.user.email)
            print(recipient_email)
            is_doctor = recipient_email == request.user.email

            subject = f"Your Analysis Report - ID #{analysis.id}" if is_doctor else "Your X-ray Analysis Report from Your Doctor"

            if is_doctor:
                # Email body for doctor
                body = f"""
                Hello Dr. {request.user.first_name} {request.user.last_name},
                
                Here is your analysis report:
                
                Date & Time: {analysis.date_time.strftime('%Y-%m-%d %H:%M')}
                Is Corrected: {'Yes' if analysis.is_corrected else 'No'}
                
                Predictions:
                {', '.join(p.result_prediction for p in analysis.predictions.all())}
                
                Note:
                {analysis.note or "No notes available."}
                
                Report Analysis:
                {analysis.report_analysis or "No report provided."}
                
                Regards,  
                Backupdoc Team
                """
            else:
                # Email body for patient
                body = f"""
                Hello,
                
                Your doctor has shared your X-ray analysis report with you.
                
                Date & Time: {analysis.date_time.strftime('%Y-%m-%d %H:%M')}
                
                Findings:
                {', '.join(p.result_prediction for p in analysis.predictions.all())}
                
                Doctor's Note:
                {analysis.note or "No notes provided."}
                
                Summary:
                {analysis.report_analysis or "No summary available."}
                
                Please consult your doctor for more information.
                
                Best regards,  
                Backupdoc Team
                """

            email = EmailMessage(subject=subject, body=body, to=[recipient_email])

            domain = getattr(settings, "DOMAIN", "http://127.0.0.1:8000")

            if analysis.raw_image:
                raw_url = f"{domain}/media/{analysis.raw_image.lstrip('/')}"
                raw_response = alpha_request.get(raw_url)
                if raw_response.status_code == 200:
                    email.attach("raw_image.jpg", raw_response.content, 'image/jpeg')

            if analysis.analyzed_image:
                analyzed_url = f"{domain}/media/{analysis.analyzed_image.lstrip('/')}"
                analyzed_response = alpha_request.get(analyzed_url)
                if analyzed_response.status_code == 200:
                    email.attach("analyzed_image.jpg", analyzed_response.content, 'image/jpeg')

            email.send()
            return Response({'message': f'Analysis report emailed to {recipient_email}.'}, status=status.HTTP_200_OK)

        except Analysis.DoesNotExist:
            return Response({'error': 'Analysis not found or not owned by you.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
