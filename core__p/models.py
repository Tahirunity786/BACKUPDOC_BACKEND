import random
import string
from django.db import models
from django.contrib.auth import get_user_model
# from core_engine.models import Predictions
User = get_user_model()

# Create your models here.
class PatientXray(models.Model):
    _id = models.CharField(max_length=50, db_index=True,default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True, blank=True)
    image = models.ImageField(upload_to='patients/Xrays', default=None, db_index=True)
    is_annovated = models.BooleanField(default=False, db_index=True,)
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
    
    patient_xrays = models.ManyToManyField(PatientXray, default='')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    first_name = models.CharField(max_length=100, db_index=True,default='')
    last_name = models.CharField(max_length=100, db_index=True,default='')
    date_of_birth = models.DateField(db_index=True, default=None)
    patient_ssn = models.CharField(max_length=50, db_index=True, unique=True)
    gender = models.CharField(max_length=50, choices=GENDER,db_index=True,default='')
    
    def save(self, *args, **kwargs):
        if not self._id:
            unique_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            self._id = f'bud-patient-{unique_str}'
        super(Patients, self).save(*args, **kwargs)