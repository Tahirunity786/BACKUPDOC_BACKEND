import random
import string
from django.db import models
from django.contrib.auth import get_user_model

from core__a.models import DoctorTimeSlots
# from core_engine.models import Predictions
User = get_user_model()

# Create your models here.
class PatientXray(models.Model):
    _id = models.CharField(max_length=50, db_index=True,default='')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, null=True, blank=True)
    image = models.ImageField(upload_to='patients/Xrays', default=None, db_index=True)
    x_image = models.ImageField(upload_to='patients/Xrays', default=None, db_index=True, null=True, blank=True)
    is_annovated = models.BooleanField(default=False, db_index=True,)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    # labels = models.ManyToManyField(Predictions, default='', db_index=True)


    def save(self, *args, **kwargs):
        if not self._id:
            unique_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            self._id = f'bud-img-{unique_str}'
        super(PatientXray, self).save(*args, **kwargs)


class Patients(models.Model):
    GENDER = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Not Confirmed', 'Not Confirmed'),
    )
    _id = models.CharField(max_length=50, db_index=True,default='')
    patient_xrays = models.ManyToManyField(PatientXray, default='', blank=True)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    first_name = models.CharField(max_length=100, db_index=True,default='')
    last_name = models.CharField(max_length=100, db_index=True,default='')
    age = models.PositiveIntegerField(default=0, db_index=True)
    gender = models.CharField(max_length=50, choices=GENDER,db_index=True,default='')
    
    def save(self, *args, **kwargs):
        if not self._id:
            unique_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            self._id = f'bud-patient-{unique_str}'
        super(Patients, self).save(*args, **kwargs)

class Appointments(models.Model):
    full_name = models.CharField(max_length=100, db_index=True)
    patient = models.ForeignKey(User, on_delete=models.CASCADE,null=True, blank=True, related_name="patient_appoint", db_index=True)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE,null=True, blank=True, related_name="doctor_appoint", db_index=True)
    email = models.EmailField(db_index=True)
    date = models.DateField(db_index=True)
    slot = models.ForeignKey(DoctorTimeSlots, on_delete=models.CASCADE, related_name='appointments', db_index=True)
    status = models.CharField(max_length=100, choices=(('pending', 'pending'),('approved', 'approved'),('declined', 'declined'), ('resolved', 'resolved')), db_index=True, default="NA")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ['-date', 'slot__start_time']
        unique_together = ('email', 'date', 'slot')

    def __str__(self):
        return f"{self.full_name} | {self.date} | {self.slot.start_time} - {self.slot.end_time}"

class AppointmentFeedback(models.Model):
    rated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedbacks_given',
        db_index=True
    )
    appointment = models.ForeignKey(
        'Appointments',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        db_index=True
    )
    rating = models.PositiveSmallIntegerField(
        default=0,
        db_index=True
    )
    description = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = "Appointment Feedback"
        verbose_name_plural = "Appointment Feedbacks"
        ordering = ['-created_at']
        unique_together = ('rated_by', 'appointment')  # Ensures one feedback per appointment per user

    def __str__(self):
        return f"Feedback by {self.rated_by.first_name} for Appointment #{self.appointment.id} - {self.rating}★"