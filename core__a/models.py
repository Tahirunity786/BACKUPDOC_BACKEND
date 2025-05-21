import random
import string
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from core__a.manager import CustomUserManager



class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ("patient", "patient"),
        ("doctor", "doctor"),
    )
    
    ACCOUNT_TYPE_CHOICES = (
        ("Free", "Free"),
        ("Doctor", "Doctor"),
        ("Premium", "Premium"),
    )
    _id = models.CharField(max_length=100, db_index=True, null=True, unique=True, default="")
    profile_url = models.ImageField(upload_to="profile/images", db_index=True, blank=True, null=True)
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    username = models.CharField(max_length=300, null=True, db_index=True, blank=True)
    email = models.EmailField(null=False, unique=True, db_index=True)
    otp = models.PositiveIntegerField(null=True, db_index=True)
    otp_limit = models.IntegerField(null=True, db_index=True)
    otp_delay = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True, db_index=True)
    last_login = models.DateTimeField(default=None, null=True, db_index=True)
    is_blocked = models.BooleanField(default=False, null=True, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES, default='patient', db_index=True)
    password = models.CharField(max_length=200, db_index=True, default=None)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # For Doctor user
    city = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    country = models.CharField(max_length=100,  db_index=True, null=True, blank=True)
    state= models.CharField(max_length=100, db_index=True, null=True, blank=True)
    street_address = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    zip_code = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    specialization = models.CharField(max_length=100, db_index=True, null=True, blank=True)

    users_messaging_container = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='messaging_container')

    objects = CustomUserManager()

    groups = models.ManyToManyField(Group, related_name='user_groups', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='user_permissions', blank=True)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self._id:
            unique_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            self._id = f'bud-{unique_str}'
        
        super(User, self).save(*args, **kwargs)



class ContactTicket(models.Model):
    contact_id = models.CharField(max_length=100, db_index=True, null=True, unique=True, default="")
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    subject = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    employee_number = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.contact_id:
            unique_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            self.contact_id = f'ct-{unique_str}'
        
        super(ContactTicket, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject} - {self.user.email}"

class Cities(models.Model):
    city_id = models.CharField(max_length=100, db_index=True, null=True, unique=True, default="", blank=True)
    city_name = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)

    def save(self, *args, **kwargs):
        if not self.city_id:
            unique_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
            self.city_id = f'ct-{unique_str}'
        
        super(Cities, self).save(*args, **kwargs)

class DoctorTimeSlots(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slotes',db_index=True)
    days = models.CharField(max_length=100, db_index=True, choices=[
        ('monday', 'monday'),
        ('tuesday', 'tuesday'),
        ('wednesday', 'wednesday'),
        ('thursday', 'thursday'),
        ('friday', 'friday'),
        ('saturday', 'saturday'),
        ('sunday', 'sunday')
    ], default='monday')

    start_time = models.TimeField(db_index=True)
    end_time = models.TimeField(db_index=True)
    is_booked = models.BooleanField(default=False,db_index=True)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)
    updated_at = models.DateTimeField(auto_now=True,db_index=True)

    class Meta:
        verbose_name = "Doctor Time Slot"
        verbose_name_plural = "Doctor Time Slots"
        ordering = [ 'start_time']


    def __str__(self):
        return f"{self.doctor.first_name} | {self.start_time} - {self.end_time}"