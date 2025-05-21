
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import Response
from rest_framework import status, throttling
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
import os
import random
import string
import requests as http_requests
from urllib.parse import urlparse
from google.oauth2 import id_token
from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework import generics
from django.db.models import Q


from core__a.serializers import ChangePasswordSerializer,CitiesSerializer, ContactTicketSerializer, CreateUserSerializer, DoctorSlotsSerializer, DoctorUserSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PatientModelUpdateSerializer, UserInfoSerializer
from core__a.token import get_tokens_for_user
from core__a.models import ContactTicket, Cities, DoctorTimeSlots
User = get_user_model()

import logging
logger = logging.getLogger(__name__)


# Too stoping the user from sending too many requests to the server

class ContactTicketRateThrottle(throttling.UserRateThrottle):
    """
    Custom throttle class to limit contact ticket creation rate.
    For example: 5 requests per hour per user.
    """
    rate = '5/hour'  # You can adjust this value as needed

class Register(APIView):
    permission_classes = [AllowAny]

    def error_format(self, errors):
        error_messages = []

        for field, field_errors in errors.items():
            if field == 'non_field_errors':
                for error in field_errors:
                    error_messages.append(str(error))  # Convert ErrorDetail to string
            else:
                for error in field_errors:
                    error_messages.append(str(error))  # Convert ErrorDetail to string

        return error_messages
    
    def post(self, request):
        
        user_serializer = CreateUserSerializer(data=request.data)
        
        if user_serializer.is_valid():
            try:
                with transaction.atomic():  # Ensure the transaction is handled properly
                    current_user = user_serializer.save()
                
                token = get_tokens_for_user(current_user)
                user = UserInfoSerializer(current_user).data

                return Response({"token":token['access'], "user":user, 'user_type':current_user.user_type, "user_id":current_user.id}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailChecker(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', None)

        if not email:
            return Response({"success": False, "message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Use cache to store and retrieve email checks to reduce database hits
        cache_key = f"email_exists_{email}"
        email_exists = cache.get(cache_key)

        if email_exists is None:
            email_exists = User.objects.filter(email=email).exists()
            # Cache the result for a certain period
            cache.set(cache_key, email_exists, timeout=60*5)  # Cache for 5 minutes

        if email_exists:
            return Response({"success": False, "message": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"success": True}, status=status.HTTP_202_ACCEPTED)

        
                
       
class UserLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password")

        if not email or not password:
            return Response({"errors": ["Email and password are required"]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"errors": ["Email for this user not found"]}, status=status.HTTP_400_BAD_REQUEST)
            
        authenticated_user = authenticate(request, username=email, password=password)
        if authenticated_user is None:
            return Response({"errors": ["Invalid credentials"]}, status=status.HTTP_401_UNAUTHORIZED)

        # if authenticated_user.is_blocked:
        #     return Response({"errors": ["Account banned"]}, status=status.HTTP_400_BAD_REQUEST)

        token = get_tokens_for_user(authenticated_user)
        user = UserInfoSerializer(authenticated_user).data

       
        return Response({"token":token['access'], "user":user, 'user_type':authenticated_user.user_type, "user_id":authenticated_user.id}, status=status.HTTP_202_ACCEPTED)
    

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request, *args, **kwargs):
        user = request.user

        serializer = PatientModelUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            current_data = serializer.save()
            file = request.FILES.get('profile')

            if file:
                current_data.profile_url = file
                current_data.save()
            
            return Response({"Success": True, "Info": "Profile updated successfully.", 'user':UserInfoSerializer(current_data).data, 'user_type':current_data.user_type}, status=status.HTTP_200_OK)
        
        errors = serializer.errors
        
        
        return Response({"Success": False, "Error": errors}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"Success": True, "Info": "Password updated successfully."}, status=status.HTTP_200_OK)
        
        return Response({"Success": False, "Error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token_value = request.data.get('idToken')
        if not id_token_value:
            return Response(data={"error": "ID token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the ID token
            id_info = id_token.verify_oauth2_token(id_token_value, requests.Request())
            user_email = id_info.get('email')
            user_image_url = id_info.get('picture')
            name = id_info.get('name')

            if not user_email:
                return Response(data={"error": "Email not found in token"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate a random password and filename
            random_password = self._generate_random_string(12)
            random_filename = self._generate_random_string(12)

            # Check if the user exists or create a new one
            user, created = User.objects.get_or_create(
                email=user_email,
                defaults={
                    'username': user_email.split('@')[0],
                    'password': random_password,
                    'full_name': name,
                    'is_buyer': True
                }
            )

            # Handle profile picture download and save
            if created:
                if user_image_url:
                    download_successful, file_path = self._download_profile_image(user_image_url, random_filename)
                    if download_successful:
                        user.profile = os.path.basename(file_path)
                        user.save()
                    else:
                        return Response(data={"error": "Unable to download profile picture"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate token and prepare response
            token = self._get_tokens_for_user(user)
            response_data = self._prepare_response_data(user, created, token)

            return Response(data=response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(data={"error": f"Invalid token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def _generate_random_string(self, length):
        """Generate a random string of letters and digits."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _download_profile_image(self, image_url, filename):
        """Download the user's profile picture and save it locally."""
        try:
            response = http_requests.get(image_url)
            if response.status_code == 200:
                parsed_url = urlparse(image_url)
                file_extension = os.path.splitext(parsed_url.path)[1] or '.jpg'
                file_path = os.path.join(settings.MEDIA_ROOT, filename + file_extension)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return True, file_path
        except Exception as e:
            return False, str(e)
        return False, None

    def _get_tokens_for_user(self, user):
        """Generate authentication tokens for the user."""
        # Assuming you have a method to generate tokens
        return get_tokens_for_user(user)

    def _prepare_response_data(self, user, is_created, token):
        """Prepare response data with user information and token."""
        return {
            'response': 'Account Created' if is_created else 'Account Logged In',
            'id': user.id,
            'username': user.username,
            'profile_image': user.profile.url if user.profile else None,
            'email': user.email,
            'token': token
        }

class UpdatePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password", "").strip()
        new_password = request.data.get("new_password", "").strip()
        confirm_password = request.data.get("confirm_password", "").strip()

        if not current_password or not new_password or not confirm_password:
            return Response(
                {"error": "All fields are required", "success": False},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not check_password(current_password, user.password):
            return Response(
                {"error": "Current password is incorrect", "success": False},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if new_password != confirm_password:
            return Response(
                {"error": "New password and confirmation do not match", "success": False},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user)
        except Exception as e:
            return Response(
                {"error": e.messages, "success": False},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password updated successfully", "success": True},
            status=status.HTTP_200_OK
        )



class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "If an account exists, a password reset link has been sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ContactTicketListCreateView(generics.ListCreateAPIView):
    """
    GET: Return a list of all contact tickets.
    POST: Create a new contact ticket and notify admin via email.
    """
    queryset = ContactTicket.objects.all().order_by('-created_at')
    serializer_class = ContactTicketSerializer
    throttle_classes = [ContactTicketRateThrottle]  # Apply throttling

    def create(self, request, *args, **kwargs):
        """
        Handle ticket creation with email notification and custom response.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Send email notification to admin
        subject = f"New Contact Ticket: {serializer.validated_data.get('subject')}"
        message = (
            f"A new contact ticket has been submitted:\n\n"
            f"Name: {serializer.validated_data.get('first_name')} {serializer.validated_data.get('last_name')}\n"
            f"Subject: {serializer.validated_data.get('subject')}\n"
            f"Message: {serializer.validated_data.get('message')}\n\n"
            f"Company: {serializer.validated_data.get('company_name') or 'N/A'}\n"
            f"Employee #: {serializer.validated_data.get('employee_number') or 'N/A'}\n"
        )
        admin_email = 'tahirunity786@gmail.com'

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Ensure this is set in your settings.py
            [admin_email],
            fail_silently=False,
        )

        return Response(
            {
                "message": "Contact ticket created successfully.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
class SearchDoctorByCityView(generics.ListAPIView):
    """
    API view to search for doctors by city.
    """
    serializer_class = UserInfoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        city = self.request.query_params.get('city', None)
        if city:
            return User.objects.filter(city__iexact=city, user_type='doctor')
        return User.objects.none()  # Return an empty queryset if no city is provided

class CitySearchAPIView(generics.ListAPIView):
    """
    API view to search cities based on partial name matches.
    Accepts a query parameter ?search= to filter cities.
    """
    serializer_class = CitiesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get('search', '').strip()
        if query:
            return Cities.objects.filter(Q(city_name__icontains=query)).order_by('city_name')[:10]
        return Cities.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Override to return a clean list of cities.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class DoctorListByCityAPIView(APIView):
    """
    API endpoint to retrieve all doctor users filtered by city name.
    Accepts a 'city' query parameter (case-insensitive).
    Returns a list of doctor users in the specified city.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        city = request.query_params.get('city', '').strip()
        if not city:
            return Response(
                {"detail": "City query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter for active, verified doctors in the given city (case-insensitive)
        doctors = User.objects.filter(
            user_type='doctor',
            city__iexact=city,
            is_active=True,
         
        )

        serializer = DoctorUserSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ALLDoctorListAPIView(generics.ListAPIView):
    serializer_class = DoctorUserSerializer
    queryset = User.objects.filter(user_type='doctor', is_active=True, is_verified=True)
    permission_classes = [AllowAny]
    pagination_class = None  


class DoctorTimeSlotsCreate(generics.ListCreateAPIView):
    serializer_class = DoctorSlotsSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        # Return only slots created by the logged-in doctor
        return DoctorTimeSlots.objects.filter(doctor=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign the logged-in user as the doctor
        serializer.save(doctor=self.request.user)
    
