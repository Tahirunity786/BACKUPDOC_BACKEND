
from django.contrib import admin
from .models import DoctorTimeSlots
from .models import DoctorTimeSlots, User,ContactTicket, Cities
# Register your models here.

admin.site.register(User)
admin.site.register(ContactTicket)
admin.site.register(Cities)
admin.site.register(DoctorTimeSlots)
