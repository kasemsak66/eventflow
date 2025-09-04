from django.contrib.auth.models import AbstractUser , BaseUserManager
from django.db import models
from django.conf import settings

# Manager สำหรับ CustomUser ใช้จัดการการสร้าง user และ superuser
class CustomUserManager(BaseUserManager):
    # ฟังก์ชันสร้าง user ธรรมดา
    def create_user(self, email, password=None, **extra_fields):
        # ถ้าไม่กรอก email ให้ error เพราะระบบนี้ login ด้วย email
        if not email:
            raise ValueError('Users must have an email address')
        
        # ปรับ format ของ email ให้เป็นมาตรฐาน (เช่น เปลี่ยนเป็น lowercase)
        email = self.normalize_email(email)
        
        # สร้าง instance ของ user โดยใส่ email + ข้อมูลเพิ่มเติม
        user = self.model(email=email, **extra_fields)
        
        # เข้ารหัส password ด้วย hashing ของ Django
        user.set_password(password)
        
        # บันทึกลง DB (using=self._db หมายถึงใช้ database connection ที่ active อยู่)
        user.save(using=self._db)
        return user

    # ฟังก์ชันสร้าง superuser (admin)
    def create_superuser(self, email, password=None, **extra_fields):
        # กำหนดค่าเริ่มต้น is_staff=True และ is_superuser=True
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # ตรวจสอบว่าค่า is_staff ต้องเป็น True เท่านั้น
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        
        # ตรวจสอบว่าค่า is_superuser ต้องเป็น True เท่านั้น
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # เรียกใช้ create_user ในการสร้าง superuser จริง
        return self.create_user(email, password, **extra_fields)


# Custom User Model แทนที่ AbstractUser (ปิดการใช้ username, ใช้ email แทน)
class CustomUser(AbstractUser):
    username = None  # ปิดการใช้งาน username
    id = models.AutoField(primary_key=True)  # Primary Key
    email = models.EmailField(unique=True)  # email ห้ามซ้ำ ใช้แทน username
    phone_num = models.CharField(max_length=15, null=False, blank=False)  # เบอร์โทร
    dob = models.DateField(null=False, blank=False)  # วันเกิด
    date_joined = models.DateTimeField(auto_now_add=True)  # วันเวลาที่สมัครสมาชิก
    
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="ชื่อธนาคาร") 
    bank_account_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="เลขบัญชี")

    # กำหนดว่าใช้ email เป็น field สำหรับ login
    USERNAME_FIELD = 'email'
    # field ที่ต้องกรอกเพิ่มเติมตอนสร้าง superuser
    REQUIRED_FIELDS = ['first_name', 'last_name']

    # ผูกกับ CustomUserManager ด้านบน
    objects = CustomUserManager() #type: ignore

    # เวลา print object จะแสดง email
    def __str__(self):
        return self.email
    

class Venue(models.Model):                                   # สร้างโมเดลสถานที่ (Venue) โดยสืบทอดจาก models.Model
    venue_id = models.AutoField(primary_key=True)  # PK ชัดเจน  # สร้างคีย์หลักแบบ Auto เพิ่มเลขอัตโนมัติและใช้เป็น Primary Key
    name = models.CharField(max_length=200)                   # ชื่อสถานที่ เก็บเป็นข้อความยาวสุด 200 ตัวอักษร
    description = models.TextField(blank=True)                # รายละเอียดเป็นข้อความยาว อนุญาตให้ว่างได้
    address = models.CharField(max_length=300, blank=True)    # ที่อยู่ เป็นข้อความยาวสุด 300 ตัวอักษร อนุญาตให้ว่างได้
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0) #type:  ignore
    extra_amenities = models.TextField(blank=True)            # รายการสิ่งอำนวยความสะดวกเพิ่มเติมเป็นข้อความยาว อนุญาตให้ว่างได้

    max_capacity = models.PositiveIntegerField(null=True, blank=True, help_text="จำนวนผู้เข้าร่วมสูงสุดที่รองรับ")  
    # ความจุสูงสุดของสถานที่ เป็นจำนวนเต็มไม่ติดลบ อนุญาตให้เป็นค่าว่าง (NULL) และไม่กรอกได้ (blank)

    owner = models.ForeignKey(                               # เจ้าของสถานที่ เป็น ForeignKey ไปยังตารางผู้ใช้
        settings.AUTH_USER_MODEL,                            # อ้างอิงโมเดลผู้ใช้ที่ตั้งใน AUTH_USER_MODEL (CustomUser ของคุณ)
        on_delete=models.CASCADE,                            # ถ้าผู้ใช้ถูกลบ ให้ลบ Venue ที่เกี่ยวข้องด้วย
        related_name='venues')                               # ชื่อ reverse relation จากผู้ใช้มายังรายการสถานที่: user.venues

    def __str__(self):                                       # เมธอดแปลงอ็อบเจ็กต์เป็นสตริงเวลาพิมพ์/แสดงในแอดมิน
        return self.name                                     # คืนค่าชื่อสถานที่

    @property                                                # กำหนดให้เมธอดด้านล่างเรียกใช้เป็นพร็อพเพอร์ตี (ไม่ต้องใส่วงเล็บ)
    def cover_image_url(self):                               # หารูป cover ของสถานที่ (รูปแรกตามลำดับ)
        first = self.images.order_by('order', 'id').first()#type:  ignore  # ดึงรูปภาพที่ related_name='images' เรียงตาม order แล้ว id และเอาอันแรก
        return first.image.url if first else None            # ถ้ามีรูปแรก คืน URL ไฟล์รูป ไม่งั้นคืน None


class VenueAmenity(models.Model):                            # โมเดลเก็บสิ่งอำนวยความสะดวกของสถานที่
    venue = models.OneToOneField(                            # ผูกแบบหนึ่งต่อหนึ่งกับ Venue (หนึ่งสถานที่มีแถวเดียวของ amenity)
        Venue,                                               # อ้างถึงตาราง Venue
        on_delete=models.CASCADE,                            # ถ้า Venue ถูกลบ ให้ลบแถว amenity นี้ด้วย
        primary_key=True,     # ใช้ venue_id เป็น PK          # ใช้คอลัมน์นี้เป็น Primary Key (จะซ้ำกับ PK ของ Venue)
        db_column='venue_id'                                 # ชื่อคอลัมน์ในฐานข้อมูลเป็น 'venue_id'
    )
    wifi = models.BooleanField(default=False)                # มี Wi-Fi หรือไม่ (ค่าเริ่มต้น False)
    parking = models.BooleanField(default=False)             # ที่จอดรถ
    equipment = models.BooleanField(default=False)           # อุปกรณ์กีฬา/อุปกรณ์ต่าง ๆ
    sound_system = models.BooleanField(default=False)        # ระบบเสียง
    projector = models.BooleanField(default=False)           # โปรเจกเตอร์
    air_conditioning = models.BooleanField(default=False)    # แอร์
    seating = models.BooleanField(default=False)             # เก้าอี้/โต๊ะ
    drinking_water = models.BooleanField(default=False)      # เครื่องกดน้ำ/น้ำดื่ม
    first_aid = models.BooleanField(default=False)           # ชุดปฐมพยาบาล
    cctv = models.BooleanField(default=False)                # กล้องวงจรปิด

    def __str__(self):                                       # เมธอดแสดงผลเป็นข้อความ
        return f"Amenities for {self.venue.name}"            # คืนข้อความบอกว่าเป็นสิ่งอำนวยความสะดวกของสถานที่ใด


class VenueImage(models.Model):                              # โมเดลเก็บรูปภาพของสถานที่ (หนึ่งสถานที่มีได้หลายรูป)
    venue = models.ForeignKey(                               # ความสัมพันธ์หลายต่อหนึ่งกับ Venue
        Venue,                                               # อ้างถึงตาราง Venue
        on_delete=models.CASCADE,                            # ถ้า Venue ถูกลบ ให้ลบรูปที่เกี่ยวข้องทั้งหมด
        related_name='images',                               # ชื่อ reverse relation: venue.images
        db_column='venue_id'                                 # ชื่อคอลัมน์ในฐานข้อมูล 'venue_id'
    )
    image = models.ImageField(upload_to='venue_images/')     # ฟิลด์รูปภาพ อัปโหลดเก็บในโฟลเดอร์ media/venue_images/
    order = models.PositiveIntegerField(null=True, blank=True)  # ลำดับการแสดงผลของรูป อนุญาตให้ว่างได้

    class Meta:                                              # เมทาดาทา (การตั้งค่าระดับคลาสของโมเดล)
        ordering = ['order', 'id']                           # ค่าเริ่มต้นเวลา query จะเรียงตาม order ก่อน จากนั้นตาม id

    def __str__(self):                                       # เมธอดแสดงผลเป็นข้อความ
        return f"Image of {self.venue.name} (order {self.order})"  # แสดงว่าเป็นรูปของสถานที่ใดและลำดับเท่าไร

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รออนุมัติ'),                     # รอเจ้าของพิจารณา
        ('approved', 'รอชำระเงิน'),                   # เจ้าของอนุมัติรอบแรก
        ('awaiting_confirmation', 'รอเจ้าของยืนยัน'), # ผู้ใช้แนบสลิปแล้ว
        ('completed', 'เสร็จสิ้น'),                   # เจ้าของอนุมัติรอบสอง
        ('rejected', 'ถูกปฏิเสธ'),
        ('cancelled', 'ยกเลิกแล้ว'),
    ]

    booking_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    payment_slip = models.ImageField(
        upload_to='payment_slips/',
        blank=True,
        null=True,
        help_text="แนบสลิปการชำระเงิน"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} จอง {self.venue.name} [{self.start_date} - {self.end_date}]"
    

