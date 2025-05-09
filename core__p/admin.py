from django.contrib import admin
from .models import PatientXray, Patients
# Register your models here.


admin.site.register(PatientXray)
admin.site.register(Patients)