from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout,authenticate
from django.db.models import Q
from .models import Room, Topic, Message, User
from .forms import RoomForm, MessageForm, UserForm, MyUserCreationForm


# Create your views here.


def loginPage(req):
    page = 'login'
    if req.user.is_authenticated:
        return redirect('home')
    if req.method == 'POST':
        email = req.POST.get('email').lower()
        password = req.POST.get('password')
        try: 
            user = User.objects.get(email=email)
        except:
            messages.error(req, "User does not exist")

        user = authenticate(req, email=email, password=password)

        if user is not None:
            login(req, user)
            return redirect('home')
        else:
            messages.error(req, "Email or Password is incorrect")

    context = {'page': page}
    return render(req, 'base/login_register.html',context)

def logoutUser(req):
    logout(req)
    return redirect('home')


def registerPage(req):
    form = MyUserCreationForm()
    if req.method == 'POST':
        form = MyUserCreationForm(req.POST)
        if form.is_valid():
            user = form.save(commit=False) #this line for not saving the form to the database until we make the next step which is converting the username to lowercase
            user.username = user.username.lower()
            user.save()
            login(req, user)
            return redirect('home')
        else:
            messages.error(req, "An error occured during registration")

    return render(req, 'base/login_register.html', {'form': form})

def home(req):
    q = req.GET.get('q') if req.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q) | Q(host__username__icontains=q)
        )
    room_cout = rooms.count()
    topics = Topic.objects.all()[0:3]
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_cout,
        'room_messages': room_messages,
    }
    return render(req, 'base/home.html', context)

def room(req, pk):

    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    if req.method == 'POST':
        message = Message.objects.create(
            user = req.user,
            room = room,
            body = req.POST.get('body')
        )
        room.participants.add(req.user)
        return redirect('room', pk=room.id)

    context = {
            'room': room,
            'room_messages': room_messages,
            'participants': participants,
    }
    
    return render(req, 'base/room.html', context)


def userProfile(req,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'room_messages': room_messages, 'topics': topics ,'rooms': rooms}
    return render(req, 'base/profile.html',context)


@login_required(login_url='login')
def createRoom(req):
    form = RoomForm()
    room_topics = Topic.objects.all()
    if req.method == 'POST':
        topics_name = req.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topics_name)
        Room.objects.create(
            host= req.user,
            topic = topic,
            name = req.POST.get('name'),
            description = req.POST.get('description')
        )
        return redirect('home')
    context = {'form': form, 'room_topics': room_topics}

    return render(req, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(req, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    room_topics = Topic.objects.all()
    if req.user != room.host:
        return HttpResponse('You are not allowed here')

    if req.method == 'POST':
        topics_name = req.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name= topics_name)
        room.name = req.POST.get('name')
        room.description = req.POST.get('description')
        room.topic = topic
        room.save()
        return redirect('home')
    context = {'form': form, 'room_topics': room_topics, 'room': room}
    return render(req, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(req,pk):
    room = Room.objects.get(id=pk)
    if req.user != room.host:
        return HttpResponse('You are not allowed here')
    
    if req.method == 'POST':
        room.delete()
        return redirect('home')
    context = {'obj': room}
    return render(req, 'base/delete.html', context )



@login_required(login_url='login')
def deleteMessage(req,pk):
    message = Message.objects.get(id=pk)
    if req.user != message.user:
        return HttpResponse('You are not allowed here')
    
    if req.method == 'POST':
        message.delete()
        return redirect('home')
    context = {'obj': message}
    return render(req, 'base/delete.html', context )


@login_required(login_url='login')
def updateMessage(req, pk):
    message = Message.objects.get(id=pk)
    form = MessageForm(instance=message)

    if req.user != message.user:
        return HttpResponse('You are not allowed here')

    if req.method == 'POST':
        form = MessageForm(req.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect('home')
    context = {'message': message, 'form': form}
    return render(req, 'base/room_form.html', context)

@login_required(login_url='login')
def updateUser(req):
    user = req.user
    form = UserForm(instance=user) #the useage of instance is to fill the form with the current data of the user
    if req.method == 'POST':
        form = UserForm(req.POST, req.FILES,instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    return render(req, 'base/update-user.html', {'form': form})

def topicsPage(req):
    q = req.GET.get('q') if req.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(req, 'base/topics.html', {'topics': topics})  #notice that the second parameter is resbosnisble for sending the data to the template


def activityPage(req):
    room_messages = Message.objects.all()
    return render(req, 'base/activity.html', {"room_messages": room_messages})