from mylogin.models import Booking


def _completed_status_value():
    """ดึงค่า status 'completed' ของ Booking ที่โปรเจกต์คุณใช้อยู่ (enum/str)"""
    return getattr(getattr(Booking, 'Status', None), 'COMPLETED', 'completed')