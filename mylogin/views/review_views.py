# mylogin/views/review_views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView

from mylogin.models import Venue, Review, Booking
from mylogin.forms import ReviewForm


def user_can_review_venue(user, venue):
    """
    เงื่อนไขว่า user รีวิวสถานที่นี้ได้ไหม:
    - ต้องเคยมี Booking ของ venue นี้
    - และสถานะเป็น completed อย่างน้อย 1 ครั้ง
    """
    if not user.is_authenticated:
        return False

    return Booking.objects.filter(
        user=user,
        venue=venue,
        status='completed', 
    ).exists()


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'review/createReview.html'

    def dispatch(self, request, *args, **kwargs):
        # ดึง venue จาก URL: /venues/<venue_id>/reviews/create/
        self.venue = get_object_or_404(Venue, pk=self.kwargs['venue_id'])

        # ไม่ให้เจ้าของรีวิวสถานที่ตัวเอง 
        if request.user == self.venue.owner:
            messages.error(request, "คุณไม่สามารถรีวิวสถานที่ของตัวเองได้")
            return redirect('venue_detail', pk=self.venue.pk)

        # เช็กว่ามี booking completed หรือยัง
        if not user_can_review_venue(request.user, self.venue):
            messages.error(request, "คุณต้องเคยจองและเสร็จสิ้นการใช้งานสถานที่นี้ก่อน จึงจะรีวิวได้")
            return redirect('venue_detail', pk=self.venue.pk)

        # ถ้ามีรีวิวอยู่แล้ว → เด้งไปหน้าแก้ไขแทน
        existing = Review.objects.filter(venue=self.venue, user=request.user).first()
        if existing:
            messages.info(request, "คุณเคยรีวิวสถานที่นี้แล้ว สามารถแก้ไขได้")
            return redirect('review_update', pk=existing.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.venue = self.venue
        form.instance.user = self.request.user
        messages.success(self.request, "บันทึกรีวิวเรียบร้อยแล้ว")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['venue'] = self.venue
        ctx['is_update'] = False
        return ctx

    def get_success_url(self):
        return reverse('venue_detail', kwargs={'pk': self.venue.pk})


class ReviewOwnerMixin(LoginRequiredMixin):
    """จำกัดให้ใช้ได้เฉพาะรีวิวของตัวเองเท่านั้น"""

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)


class ReviewUpdateView(ReviewOwnerMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'review/createReview.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['venue'] = self.object.venue
        ctx['is_update'] = True
        return ctx

    def get_success_url(self):
        messages.success(self.request, "แก้ไขรีวิวเรียบร้อยแล้ว")
        return reverse('venue_detail', kwargs={'pk': self.object.venue.pk})


class ReviewDeleteView(ReviewOwnerMixin, DeleteView):
    model = Review
    template_name = 'review/deleteReview.html'

    def get_success_url(self):
        messages.success(self.request, "ลบรีวิวเรียบร้อยแล้ว")
        return reverse('venue_detail', kwargs={'pk': self.object.venue.pk})
