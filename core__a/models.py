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
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='Free', null=True, db_index=True)
    credits = models.IntegerField(null=True, db_index=True,default=3)
    password = models.CharField(max_length=200, db_index=True, default=None)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

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