import uuid
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.template.loader import render_to_string

from core__a.utiles import send_password_reset_email
from core__a.models import ContactTicket

User = get_user_model()

class CreateUserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.pop('confirm_password', None)

        validate_password(password)

        if password != confirm_password:
            raise serializers.ValidationError({'password': 'Passwords do not match'})

        return data

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data.pop('email', None)
        if email is None:
            raise serializers.ValidationError({'email': 'Email field is required'})

        username = str(uuid.uuid4())
        user = User.objects.create_user(username=username, email=email, **validated_data)
        return user

class PatientModelUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("first_name", "last_name", "bio", "email")
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
            'bio': {'required': False},
        }

    def update(self, instance, validated_data):
        # Update each field in validated_data if present
        instance.profile_url = validated_data.get('profile', instance.profile_url)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.save()
        return instance
    
class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New password and confirm password must match."})
        return data


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("profile_url","first_name", "last_name")




class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if not user:
            return value  # Prevents email enumeration

        # Check OTP limit
        # if user.otp_limit is not None and user.otp_limit >= 8:
        #     raise serializers.ValidationError("You have reached the maximum password reset attempts. Please try again later or contact support.")

        # Check if a reset request was sent recently (e.g., within 10 minutes)
        # if user.otp_delay and now() - user.otp_delay < timedelta(minutes=10):
        #     raise serializers.ValidationError("A password reset link was already sent recently. Please check your email or try again later.")
        
        self.user = user
        return value

    def save(self):
        if hasattr(self, "user") and self.user:
            user = self.user
            
            # Increment OTP limit
            user.otp_limit = (user.otp_limit or 0) + 1
            user.otp_delay = now()
            user.save(update_fields=["otp_limit", "otp_delay"])
            
            # Generate reset token and link
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{settings.FRONTEND_URL}/reset-password?uuid={uid}&SIDToken={token}"

            # Send Reset Email
            subject = "Password Reset Request"
            html_content = render_to_string("email/forgotRequest.html", {
                "reset_link": reset_link,
            })

            data = {
                "subject": subject,
                "email": user.email,
                "html_content": html_content
            }
            # print("Data: ", data)
            
            send_password_reset_email(data)

        return {"message": "If an account exists, a password reset link has been sent to your email."}



    
class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            
            raise serializers.ValidationError({"password": "Passwords do not match."})

        return data

    def save(self):
        from django.utils.http import urlsafe_base64_decode
        from django.contrib.auth.tokens import default_token_generator

        uid = self.validated_data['uid']
        token = self.validated_data['token']
        new_password = self.validated_data['new_password']

        try:
            user_id = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=user_id)

            if not default_token_generator.check_token(user, token):
                raise serializers.ValidationError({"token": "Invalid or expired token."})

            user.set_password(new_password)
            print("Password: ", new_password)
            user.otp_limit = 0
            user.save(update_fields=['password', 'otp_limit'])
            print("Password reset successfully.")

            return {"message": "Password reset successfully."}

        except (User.DoesNotExist, ValueError):
            raise serializers.ValidationError({"uid": "Invalid user ID."})



class ContactTicketSerializer(serializers.ModelSerializer):
    """
    Serializer for the ContactTicket model.
    Converts model instances to and from JSON format for API interactions.
    """

    class Meta:
        model = ContactTicket
        # Fields to include in the serialized output
        fields = [
            'contact_id',
            'first_name',
            'last_name',
            'subject',
            'company_name',
            'employee_number',
            'message',
            'created_at',
            'updated_at',
            'is_resolved',
        ]
        # Read-only fields to protect from being updated by clients
        read_only_fields = ['contact_id', 'created_at', 'updated_at']