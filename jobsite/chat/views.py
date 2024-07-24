from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Room, Message

@login_required
def chat_home(request):
    return render(request, 'chat/chat_home.html')

def room_list(request):
    if request.method == "POST":
        room_name = request.POST.get('room_name')
        Room.objects.create(name=room_name)
        return redirect('room_list')
    rooms = Room.objects.all()
    return render(request, 'chat/room_list.html', {'rooms': rooms})

def room_detail(request, room_name):
    room = Room.objects.get(name=room_name)
    return render(request, 'chat/room_detail.html', {'room_name': room_name, 'room': room})
