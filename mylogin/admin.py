from django.contrib import admin
from mylogin.models import CustomUser

admin.site.register(CustomUser)
from .models import Venue, VenueAmenity, VenueImage

class VenueAmenityInline(admin.StackedInline):
    model = VenueAmenity
    can_delete = False
    max_num = 1

class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 1
    fields = ("image", "order")
    ordering = ("order", "id")
    max_num = 5

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_day")
    inlines = [VenueAmenityInline, VenueImageInline]

@admin.register(VenueImage)
class VenueImageAdmin(admin.ModelAdmin):
    list_display = ("venue", "order", "image")
    list_editable = ("order",)

@admin.register(VenueAmenity)
class VenueAmenityAdmin(admin.ModelAdmin):
    list_display = ("venue", "wifi", "parking", "equipment", "sound_system",
                    "projector","air_conditioning","seating","drinking_water","first_aid","cctv")