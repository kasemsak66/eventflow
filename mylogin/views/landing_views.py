# mylogin/views/landing_views.py
from math import radians, sin, cos, sqrt, atan2
from django.views.generic import ListView
from django.db.models import Count, Avg, Q
from django.utils import timezone
import logging
import re

from mylogin.models import Venue

logger = logging.getLogger(__name__)


def _parse_float(val):
    """Try to convert val to float. Accepts strings with commas and Decimal. Returns None on failure."""
    if val is None:
        return None
    try:
        s = str(val).strip()
        # allow both comma or dot as decimal separator from various locales/inputs
        s = s.replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return None


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """
    คำนวณระยะทางระหว่าง 2 จุด (lat/lng) หน่วย km
    """
    R = 6371.0
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


class LandingView(ListView):
    """
    หน้า Landing: ค้นหาแบบ "คัดเลือกสถานที่ที่เหมาะสม" (ไม่ใช้ keyword)
    - filter: ราคา, ความจุ, จังหวัด, อำเภอ, สิ่งอำนวยความสะดวก, ใกล้ฉัน (lat/lng + radius)
    - ส่วนล่าง: สถานที่ยอดฮิต 3 แบบ
    """
    model = Venue
    template_name = "home/landing.html"
    context_object_name = "venues"
    paginate_by = 12

    # ====== amenity fields ที่ใช้ใน VenueAmenity ======
    AMENITY_FIELDS = [
        "wifi", "parking", "equipment", "sound_system", "projector",
        "air_conditioning", "seating", "drinking_water", "first_aid", "cctv"
    ]

    def get_queryset(self):
        qs = (
            Venue.objects
            .select_related("owner")
            .prefetch_related("images", "reviews", "favorites")
        )

        # ---------- Filters ----------
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        min_capacity = self.request.GET.get("min_capacity")
        province = (self.request.GET.get("province") or "").strip()
        district = (self.request.GET.get("district") or "").strip()

        # ราคา
        if min_price:
            try:
                qs = qs.filter(price_per_day__gte=float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                qs = qs.filter(price_per_day__lte=float(max_price))
            except ValueError:
                pass

        # ความจุ
        if min_capacity:
            try:
                qs = qs.filter(max_capacity__gte=int(min_capacity))
            except ValueError:
                pass

        # จังหวัด/อำเภอ จาก address (ค้นหาจาก text ที่ user ใส่ใน `q`)
        # ถ้ามีพารามิเตอร์ q (เช่น "กรุงเทพ พญาไท") ให้ split และค้นหาจาก address ของ Venue
        q = (self.request.GET.get("q") or "").strip()
        if q:
            # แยกคำตาม whitespace/comma และกรองแบบ AND (ทุกคำต้องอยู่ใน address)
            tokens = [t for t in re.split(r"[\s,]+", q) if t]
            for t in tokens:
                qs = qs.filter(address__icontains=t)
        else:
            # ย้อนกลับไปยังการค้นหาแยก province/district ถ้าไม่มี q
            if province:
                qs = qs.filter(address__icontains=province)
            if district:
                qs = qs.filter(address__icontains=district)

        # สิ่งอำนวยความสะดวก (ต้องมี VenueAmenity ครบ)
        for field in self.AMENITY_FIELDS:
            if self.request.GET.get(field) == "1":
                qs = qs.filter(**{f"venueamenity__{field}": True})

        # ใกล้ฉัน (Near me) -> รับ lat/lng จาก JS
        near = self.request.GET.get("near") == "1"
        lat_raw = self.request.GET.get("lat")
        lng_raw = self.request.GET.get("lng")
        radius_raw = self.request.GET.get("radius_km") or "5"

        user_lat = _parse_float(lat_raw)
        user_lng = _parse_float(lng_raw)
        r_km = _parse_float(radius_raw) or 5.0

        if near and user_lat is not None and user_lng is not None:
            # ดึงเฉพาะที่มีพิกัด
            with_geo = qs.filter(latitude__isnull=False, longitude__isnull=False).values_list("venue_id", "latitude", "longitude")

            allowed_ids = []
            for vid, vlat_raw, vlng_raw in with_geo:
                try:
                    vlat = _parse_float(vlat_raw)
                    vlng = _parse_float(vlng_raw)
                    if vlat is None or vlng is None:
                        continue
                    d = haversine_km(user_lat, user_lng, vlat, vlng)
                    if d <= r_km:
                        allowed_ids.append(vid)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.exception("Error computing distance for venue %s: %s", vid, exc)
                    continue

            # ถ้า allowed_ids ว่าง = ไม่มีสถานที่ในรัศมี จะคืน queryset ว่าง
            qs = qs.filter(venue_id__in=allowed_ids)

        # เรียงผลลัพธ์ (ถ้าอยากให้เป็น “ยอดนิยม” เป็น default ก็เปลี่ยนได้)
        qs = qs.order_by("-venue_id")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ส่งค่า filter กลับไปให้ template เพื่อคงค่าเดิมในฟอร์ม
        ctx["min_price"] = self.request.GET.get("min_price", "")
        ctx["max_price"] = self.request.GET.get("max_price", "")
        ctx["min_capacity"] = self.request.GET.get("min_capacity", "")
        ctx["province"] = self.request.GET.get("province", "")
        ctx["district"] = self.request.GET.get("district", "")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["near"] = self.request.GET.get("near", "")
        ctx["radius_km"] = self.request.GET.get("radius_km", "5")
        ctx["lat"] = self.request.GET.get("lat", "")
        ctx["lng"] = self.request.GET.get("lng", "")

        # amenity selections
        selected_amenities = {f: (self.request.GET.get(f) == "1") for f in self.AMENITY_FIELDS}
        ctx["amenity_fields"] = self.AMENITY_FIELDS
        ctx["selected_amenities"] = selected_amenities

        # ====== Recommended / Hot places (3 แบบ) ======

        owner_venues = Venue.objects.all()

        # 1) ยอดฮิตจากการจองสำเร็จ (Booking.status = completed)
        ctx["hot_by_completed_booking"] = (
            owner_venues.annotate(
                completed_booking_count=Count(
                    "bookings",
                    filter=Q(bookings__status="completed")
                )
            )
            .order_by("-completed_booking_count", "-venue_id")[:6]
        )

        # 2) ยอดฮิตจากการใช้ทำกิจกรรมบ่อย (จำนวน Activity)
        ctx["hot_by_activity"] = (
            owner_venues.annotate(
                activity_count=Count("bookings__activity")
            )
            .order_by("-activity_count", "-venue_id")[:6]
        )

        # 3) ยอดฮิตจากรีวิว (Avg rating + จำนวนรีวิว)
        ctx["hot_by_review"] = (
            owner_venues.annotate(
                avg_rating=Avg("reviews__rating"),
                review_count=Count("reviews")
            )
            .order_by("-avg_rating", "-review_count", "-venue_id")[:6]
        )

        return ctx
