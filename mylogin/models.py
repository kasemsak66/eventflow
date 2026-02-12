from datetime import datetime
from time import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings
from openlocationcode import openlocationcode as olc
from django.utils import timezone
import datetime


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
    dob = models.DateField(null=True, blank=True)
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class Activity(models.Model):
    activity_id = models.AutoField(primary_key=True)

    STATUS_CHOICES = [
        ('draft', 'ร่าง (ยังไม่เปิดให้ลงทะเบียน)'),
        ('published', 'เปิดให้ลงทะเบียน'),
        ('closed', 'ปิดรับลงทะเบียน'),
        ('cancelled', 'ยกเลิกกิจกรรม'),
        ('finished', 'จบกิจกรรมแล้ว'),
    ]

    booking = models.OneToOneField(
        'Booking',
        on_delete=models.CASCADE,
        related_name='activity',
        db_column='booking_id'
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_activities'
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # ช่วงวันและเวลาจัดกิจกรรม
    # ใส่ default สำหรับ row เดิมใน DB
    start_date = models.DateField(
        default=timezone.now,
        help_text="วันที่เริ่มกิจกรรม"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="วันที่จบกิจกรรม (เว้นว่างได้ ถ้าจัดวันเดียว)"
    )

    start_time = models.TimeField(
        default=datetime.time(9, 0),  # 09:00 เป็นค่าเริ่มต้นให้ row เดิม
        help_text="เวลาเริ่มกิจกรรม"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="เวลาจบกิจกรรม (เว้นว่างได้ ถ้าไม่กำหนดชัดเจน)"
    )

    max_participants = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="จำนวนผู้เข้าร่วมสูงสุด (เว้นว่าง = ไม่จำกัด)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='published'
    )

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ActivityParticipants',
        related_name='joined_activities',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-start_time']

    def __str__(self):
        end_date = self.end_date or self.start_date
        if self.start_date == end_date:
            if self.end_time:
                return f"{self.name} ({self.start_date} {self.start_time}-{self.end_time})"
            return f"{self.name} ({self.start_date} {self.start_time})"
        else:
            return f"{self.name} ({self.start_date} - {end_date})"

    @property
    def venue(self):
        return self.booking.venue

    @property
    def current_participants_count(self):
        return self.activity_participations.filter(status='joined').count()

    @property
    def is_full(self):
        if not self.max_participants:
            return False
        return self.current_participants_count >= self.max_participants

    @property
    def has_ended(self):
        from datetime import datetime, time as dtime
        end_date = self.end_date or self.start_date
        end_time = self.end_time or self.start_time or dtime(23, 59, 59)
        end_dt = datetime.combine(end_date, end_time)
        return end_dt < datetime.now()


class ActivityParticipants(models.Model):
    STATUS_CHOICES = [
        ('joined', 'เข้าร่วม'),
        ('cancelled', 'ยกเลิก'),
    ]

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='activity_participations'
    )

    # ถ้าเป็น member (login) → user มีค่า
    # ถ้าเป็น guest (กรอกฟอร์ม) → user = None + is_manual=True
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_participations'
    )

    is_manual = models.BooleanField(
        default=False,
        help_text="True = ลงทะเบียนแบบกรอกข้อมูลมือ (guest); False = ผูกกับ user จริง"
    )

    # ข้อมูล manual สำหรับ guest
    manual_full_name = models.CharField(max_length=200, blank=True)
    manual_email = models.EmailField(blank=True)
    manual_phone = models.CharField(max_length=50, blank=True)
    manual_note = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='joined'
    )

    # เวลา “สมัครเข้าร่วม”
    joined_at = models.DateTimeField(auto_now_add=True)

    # ใช้เช็กชื่อ/มาเข้าร่วมจริง
    attended = models.BooleanField(default=False)
    attended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # 1 user 1 activity ไม่ควรมีหลายแถว (สำหรับ user ที่ล็อกอิน)
        constraints = [
            models.UniqueConstraint(
                fields=['activity', 'user'],
                condition=models.Q(user__isnull=False),
                name='unique_activity_user_participation'
            )
        ]
        ordering = ['activity', '-joined_at']

    @property
    def display_name(self):
        if self.user:
            name = f"{self.user.first_name} {self.user.last_name}".strip()
            return name or self.user.email
        return self.manual_full_name or "Guest"

    @property
    def is_guest(self):
        return self.user is None or self.is_manual

    def __str__(self):
        return f"{self.display_name} - {self.activity.name} ({self.status})"

class ChatThread(models.Model):
    venue = models.ForeignKey(
        'mylogin.Venue',
        on_delete=models.CASCADE,
        related_name='chat_threads'
    )

    # ฝั่งลูกค้า
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_threads_as_customer'
    )

    # ฝั่งเจ้าของ
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_threads_as_owner'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['venue', 'customer', 'owner'],
                name='unique_chat_thread_per_venue_customer_owner'
            )
        ]

    def __str__(self):
        return f"Chat {self.customer} ↔ {self.owner} @ {self.venue}"


class ChatMessage(models.Model):
    thread = models.ForeignKey(
        ChatThread,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_chat_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    @property
    def receiver(self):
        # อีกฝั่งของคนส่งใน thread นี้
        if self.sender_id == self.thread.owner_id:
            return self.thread.customer
        return self.thread.owner

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content[:20]}"
    
class Review(models.Model):
    RATING_CHOICES = [
        (1, "1 - แย่มาก"),
        (2, "2 - พอใช้"),
        (3, "3 - ปานกลาง"),
        (4, "4 - ดี"),
        (5, "5 - ดีมาก"),
    ]

    venue = models.ForeignKey(
        'mylogin.Venue',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('venue', 'user')  # 1 คนรีวิวสถานที่นี้ได้ 1 ครั้ง
        ordering = ['-created_at']

    def __str__(self):
        return f"Review {self.venue} by {self.user} ({self.rating})"
    
class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'venue')  # 1 คน กดใจสถานที่นึงได้ครั้งเดียว
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} ♥ {self.venue.name}"
