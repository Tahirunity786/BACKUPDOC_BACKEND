from django.contrib import admin
from .models import PatientXray, Patients, Appointments, AppointmentFeedback
# Register your models here.


admin.site.register(PatientXray)
admin.site.register(Patients)
admin.site.register(Appointments)
admin.site.register(AppointmentFeedback)