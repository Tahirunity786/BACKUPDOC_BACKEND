from rest_framework import serializers
from django.contrib.auth import get_user_model

from core__a.models import DoctorTimeSlots
from .models import AppointmentFeedback, Appointments, PatientXray, Patients

User = get_user_model()

class PatientXraySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientXray
        fields = ['_id', 'image', 'is_annovated']

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

class DoctorUserInfo(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name")

class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patients
        fields = [
            '_id',
            'first_name',
            'last_name',
            'age',
            'gender',
            'doctor'
        ]
        read_only_fields = ['_id']

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class DoctorTimeSlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorTimeSlots
        fields = ['id', 'doctor', 'date', 'start_time', 'end_time', 'is_booked']

        read_only_fields = ['id']

class AppointmentSerializer(serializers.ModelSerializer):
    # Accept slot ID for writing, but show full data when reading
    slot = serializers.PrimaryKeyRelatedField(queryset=DoctorTimeSlots.objects.all())

    class Meta:
        model = Appointments
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'id', 'doctor', 'patient']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Replace slot ID with full slot data when returning response
        rep['slot'] = DoctorTimeSlotsSerializer(instance.slot).data
        rep['doctor'] = DoctorUserInfo(instance.doctor).data
        return rep

    def validate(self, data):
        slot = data.get('slot')
        date_val = data.get('date')

        if slot and date_val and Appointments.objects.filter(slot=slot, date=date_val).exists():
            raise serializers.ValidationError("This slot is already booked.")
        return data

class AppointmentFeedbackSerializer(serializers.ModelSerializer):
    rated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = AppointmentFeedback
        fields = ['id', 'rated_by', 'appointment', 'rating', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5 stars.")
        return value

    def validate(self, data):
        user = self.context['request'].user
        appointment = data.get('appointment')

        if AppointmentFeedback.objects.filter(rated_by=user, appointment=appointment).exists():
            raise serializers.ValidationError("You have already submitted feedback for this appointment.")
        return data