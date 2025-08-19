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
    


class Venue(models.Model):
    venue_id = models.AutoField(primary_key=True)  # PK ชัดเจน
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_amenities = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='venues')

    def __str__(self):
        return self.name

    @property
    def cover_image_url(self):
        first = self.images.order_by('order', 'id').first()
        return first.image.url if first else None


class VenueAmenity(models.Model):
    venue = models.OneToOneField(
        Venue,
        on_delete=models.CASCADE,
        primary_key=True,     # ใช้ venue_id เป็น PK
        db_column='venue_id'
    )
    wifi = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    equipment = models.BooleanField(default=False)
    sound_system = models.BooleanField(default=False)
    projector = models.BooleanField(default=False)
    air_conditioning = models.BooleanField(default=False)
    seating = models.BooleanField(default=False)
    drinking_water = models.BooleanField(default=False)
    first_aid = models.BooleanField(default=False)
    cctv = models.BooleanField(default=False)

    def __str__(self):
        return f"Amenities for {self.venue.name}"


class VenueImage(models.Model):
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name='images',
        db_column='venue_id'
    )
    image = models.ImageField(upload_to='venue_images/')
    order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image of {self.venue.name} (order {self.order})"
    
    
