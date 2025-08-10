from django.contrib.auth.models import AbstractUser , BaseUserManager
from django.db import models
from django.conf import settings
from multiselectfield import MultiSelectField

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    phone_num = models.CharField(max_length=15, null=False, blank=False)
    dob = models.DateField(null=False, blank=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    

class Venue(models.Model): # เพิ่ม Extra AMENITY , เพิ่ม table amenties ,
    AMENITY_CHOICES = [
    ('wifi', 'Wi-Fi อินเทอร์เน็ต'),
    ('parking', 'ที่จอดรถ'),
    ('equipment', 'อุปกรณ์กีฬา'),
    ('sound_system', 'ระบบเสียง / ไมโครโฟน'),
    ('projector', 'โปรเจกเตอร์ / หน้าจอ'),
    ('air_conditioning', 'เครื่องปรับอากาศ'),
    ('seating', 'เก้าอี้ / โต๊ะ'),
    ('drinking_water','เครื่องกดน้ำ'),
    ('first_aid', 'ชุดปฐมพยาบาล'),
    ('cctv', 'กล้องวงจรปิด / ระบบรักษาความปลอดภัย')
]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    venue_name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    amenities = MultiSelectField(choices=AMENITY_CHOICES)
    is_active = models.BooleanField(default=True)
    time_open = models.TimeField()
    time_closed = models.TimeField()

    def __str__(self):
        return self.venue_name

class VenueImage(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='venue_images/')

    def __str__(self):
        return f"Image of {self.venue.venue_name}"
