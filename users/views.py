from django.shortcuts import render, redirect
import json
from rides.models import BookedRide
from .forms import UserRegistrationForm, CustomLoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') 
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

from django.shortcuts import render

# def login(request):
#     return render(request, 'login.html')

# from django.contrib.auth.forms import AuthenticationForm

# def login_view(request):
#     form = AuthenticationForm()
#     return render(request, 'login.html', {'form': form})

def user_login(request):
    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redirect to homepage after login
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form})


def home(request):
    return render(request, 'home.html')

@login_required()
def dashboard(request):
    return render(request, 'dashboard.html')

def profile(request):
    user = request.user
    booked_rides = BookedRide.objects.filter(user=user).select_related('ride')

    # Extract display_name from JSON fields
    for ride in booked_rides:
        try:
            pickup_data = json.loads(ride.pickup_location)
            dropoff_data = json.loads(ride.dropoff_location)
            ride.pickup_display = pickup_data.get("name", "Unknown Location")
            ride.dropoff_display = dropoff_data.get("name", "Unknown Location")
        except json.JSONDecodeError:
            ride.pickup_display = "Invalid Location Data"
            ride.dropoff_display = "Invalid Location Data"

    context = {
        "user": user,
        "booked_rides": booked_rides,
    }

    return render(request, "profile.html", context)

def user_logout(request):
    logout(request)
    return redirect('login')

