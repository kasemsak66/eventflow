# mylogin/views/chat_views.py
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from mylogin.models import Venue, ChatThread, ChatMessage


@login_required
def start_venue_chat(request, venue_id):
    """
    ถูกเรียกจากปุ่มในหน้า detailVenue
    - ถ้า customer กด → หา/สร้าง thread 1–1 กับ owner
    - แล้ว redirect ไปหน้า chat_thread_view
    """
    venue = get_object_or_404(Venue, pk=venue_id)
    owner = venue.owner
    user = request.user

    # ไม่ให้เจ้าของเปิดแชทหาตัวเองจากปุ่มนี้
    if user == owner:
        return redirect('chat_history')

    thread, created = ChatThread.objects.get_or_create(
        venue=venue,
        customer=user,
        owner=owner,
    )

    return redirect('chat_thread_view', pk=thread.pk)


@login_required
def chat_thread_view(request, pk):
    """
    แสดงหน้าแชท 1–1 ของ thread นี้
    """
    thread = get_object_or_404(ChatThread, pk=pk)

    # ให้เข้าได้เฉพาะ owner กับ customer
    if request.user not in (thread.customer, thread.owner):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าห้องแชทนี้")

    chat_messages = (
        ChatMessage.objects
        .filter(thread=thread)
        .select_related('sender')
        .order_by('timestamp')
    )

    if request.user == thread.owner:
        other_user = thread.customer
    else:
        other_user = thread.owner

    return render(request, 'chat/chat.html', {
        'thread': thread,
        'chat_messages': chat_messages,  # 👈 ชื่อ key ใช้ตัวนี้
        'other_user': other_user,
    })


@login_required
def chat_history(request):
    """
    แสดงรายการห้องแชททั้งหมดที่ user คนนี้เกี่ยวข้อง
    """
    threads = (
        ChatThread.objects
        .filter(Q(customer=request.user) | Q(owner=request.user))
        .select_related('venue', 'customer', 'owner')
        .order_by('-updated_at')
    )

    return render(request, 'chat/chat_history.html', {
        'threads': threads,
    })
