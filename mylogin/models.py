from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings
from openlocationcode import openlocationcode as olc 


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

    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="ชื่อธนาคาร")
    bank_account_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="เลขบัญชี")
    bank_qr = models.ImageField(upload_to='bank_qr/', blank=True, null=True, verbose_name="QR สำหรับโอน")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()  

    def __str__(self):
        return self.email


class Venue(models.Model):
    venue_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # type: ignore
    extra_amenities = models.TextField(blank=True)
    max_capacity = models.PositiveIntegerField(null=True, blank=True, help_text="จำนวนผู้เข้าร่วมสูงสุดที่รองรับ")

    code = models.CharField(max_length=32, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='venues'
    )

    def save(self, *args, **kwargs):
        # ตั้ง Plus Code อัตโนมัติจาก lat/lng เสมอเมื่อมีพิกัด
        if self.latitude is not None and self.longitude is not None:
            self.code = olc.encode(float(self.latitude), float(self.longitude), codeLength=10)
        else:
            # ถ้าไม่มีพิกัด ให้เคลียร์ code เพื่อไม่ให้ค้างจากเดิม
            self.code = ""
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name

    @property
    def cover_image_url(self):
        first = self.images.order_by('order', 'id').first()  # type: ignore
        return first.image.url if first else None


class VenueAmenity(models.Model):
    venue = models.OneToOneField(
        Venue,
        on_delete=models.CASCADE,
        primary_key=True,
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


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รออนุมัติ'),
        ('approved', 'รอชำระเงิน'),
        ('awaiting_confirmation', 'รอเจ้าของยืนยัน'),
        ('completed', 'เสร็จสิ้น'),
        ('rejected', 'ถูกปฏิเสธ'),
        ('cancelled', 'ยกเลิกแล้ว'),
    ]

    booking_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='bookings')

    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    payment_slip = models.ImageField(upload_to='payment_slips/', blank=True, null=True)

    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    slip_uploaded_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} จอง {self.venue.name} [{self.start_date} - {self.end_date}]"