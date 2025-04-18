import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.utils.timezone import localtime
from django.utils import timezone
from geopy.distance import geodesic  # To calculate distance
from django.db import transaction
from django.utils.timezone import now
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from .forms import BookRideForm, PlanRideForm
from .models import BookedRide, Ride, Transaction
import stripe
import requests

def plan_ride(request):
    if request.method == "POST":
        form = PlanRideForm(request.POST)
        print("Form data:", form.data)
        if form.is_valid():
            ride = form.save(commit=False)
            
            # Capture full JSON metadata from frontend
            ride.pickup_metadata = json.loads(request.POST.get("pickup_metadata", "{}"))
            ride.dropoff_metadata = json.loads(request.POST.get("dropoff_metadata", "{}"))
            
            ride.driver = request.user  # Assign logged-in user as driver
            ride.save()
            return redirect('dashboard')  # Redirect after saving ride
        else:
            print("Form errors:", form.errors)  # Debugging
    else:
        form = PlanRideForm()

    return render(request, 'PlanARide.html', {'form': form})

def get_rides_by_id(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)
    rides_data = {
            "id": ride.id,
            "pickup_location": ride.pickup_location,
            "dropoff_location": ride.dropoff_location,
            "date_time": ride.date_time.strftime("%Y-%m-%d %H:%M"),
            "available_seats": ride.available_seats,
            "price": float(ride.price),
            "pickup_metadata": ride.pickup_metadata,
            "dropoff_metadata": ride.dropoff_metadata,
        }
    return JsonResponse(rides_data, safe=False)


def get_available_rides(request):
    """
    Fetch all rides that are scheduled in the future.
    """
    future_rides = Ride.objects.filter(date_time__gt=now(), available_seats__gt=0).order_by('date_time')
    
    rides_data = [
        {
            "id": ride.id,
            "pickup_location": ride.pickup_location,
            "dropoff_location": ride.dropoff_location,
            "date_time": ride.date_time.strftime("%Y-%m-%d %H:%M"),
            "available_seats": ride.available_seats,
            "price": float(ride.price),
            "pickup_metadata": ride.pickup_metadata,
            "dropoff_metadata": ride.dropoff_metadata,
        }
        for ride in future_rides
    ]
    
    return JsonResponse(rides_data, safe=False)

def bookRide(request):
    return render(request, 'BookARide.html')

# def payment(request):
#     booking_id = request.GET.get("booking_id")
#     fare = request.GET.get("fare")
#     return render(request, "payment.html", {
#         "booking_id": booking_id,
#         "fare": fare,
#         "stripe_public_key": settings.STRIPE_PUBLIC_KEY  # Pass as context here
#     })
stripe.api_key = settings.STRIPE_SECRET_KEY

def get_location_metadata(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    response = requests.get(url)

    if response.status_code == 200:  # Ensure response is successful
        try:
            return response.json()  # Convert to JSON safely
        except requests.exceptions.JSONDecodeError:
            print(f"Invalid JSON response for {url}")
            return {}
    else:
        print(f"Error fetching location: {response.status_code}, URL: {url}")
        return {}

def get_client_ip(request):
    """Get the real IP address of the client"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]  # First IP in the list is the real client IP
    else:
        ip = request.META.get("REMOTE_ADDR")  # Fallback to REMOTE_ADDR
    return ip


def get_user_country(request):
    """Detect user's country based on IP"""
    ip = get_client_ip(request)  # Call the function to get the IP
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")  # Fetch IP details
        data = response.json()
        country_code = data.get("country", "US")  # Default to India if not found
    except Exception as e:
        print("Error getting country:", e)
        country_code = "US" 

    return country_code


def bookRideById(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)

    if request.method == "GET":
        # Step 1: Display Booking Form
        form = BookRideForm()
        user_country_code = get_user_country(request)
        return render(request, "BookARideForm.html", {"form": form, "ride": ride, "user_country_code": user_country_code})

    elif request.method == "POST":
        print(f"Received POST request: {request.content_type}")
        stripePaymentIdCheck = False
        try:
            if request.content_type == "application/json":
                body = json.loads(request.body)
                print(body, 'body')
                stripePaymentIdCheck = body["stripePaymentId"] == 'None'
            else:
                body = request.POST
                stripePaymentIdCheck = request.POST.get('stripePaymentId') != 'None'

        except json.JSONDecodeError:
            print("Error: Empty or invalid JSON received")  # Log error
            return JsonResponse({"error": "Invalid JSON"}, status=400)       

        if stripePaymentIdCheck:
            # Step 2: Handle Form Submission and Save Booking Temporarily
            form = BookRideForm(request.POST)
            ride = get_object_or_404(Ride, id=ride_id)
            print('Ride:', ride)
            if form.is_valid():
                with transaction.atomic():  # ACID compliance
                    # Save booking but don't finalize yet
                    booking = form.save(commit=False)
                    booking.user = request.user
                    booking.ride = ride

                    # Reverse geocode pickup & dropoff metadata
                    booking.pickup_location = request.POST.get("pickup_metadata", "Unknown Pickup")
                    booking.dropoff_location = request.POST.get("dropoff_metadata", "Unknown Dropoff")

                    # Save booking
                    booking.save()

                    # Redirect to Payment Page with Ride & Booking Details
                    print(settings.STRIPE_PUBLIC_KEY, 'settings.STRIPE_PUBLIC_KEY')
                    return render( request, "Payment.html",  {"booking_id" : booking.id,
                            "fare":booking.fare, 
                            "stripe_public_key": settings.STRIPE_PUBLIC_KEY}  # Pass as context, not in URL
                        )
            else:
                messages.error(request, "Invalid form submission.")
                return redirect("book_ride_by_id", ride_id=ride_id)
        else:
            # Step 3: Process Payment Upon Receiving Stripe Payment ID
            booking_id = body.get("booking_id")
            stripePaymentId = body.get("stripePaymentId")
            print(booking_id, stripePaymentId)
            booking = get_object_or_404(BookedRide, id=booking_id)
            print(booking, 'booking')
            try:
                with transaction.atomic():
                    amount = booking.fare
                    intent = stripe.PaymentIntent.create(
                        amount=int(amount),
                        currency="usd",
                        description=f"Ride Booking",
                        payment_method=stripePaymentId,
                        confirm=True,
                        automatic_payment_methods={"enabled": True, "allow_redirects": "never"}
                    )

                    if intent.status == "succeeded":
                        # Save transaction details
                        try:
                            with transaction.atomic():  # Ensure ACID compliance
                                transaction_record = Transaction.objects.create(
                                    user=request.user,
                                    ride=get_object_or_404(BookedRide, id=booking_id),
                                    amount=booking.fare,
                                    status="SUCCESS",
                                    stripe_payment_id=intent.id
                                )

                                if transaction_record:  # Only proceed if Transaction is successfully created
                                    ride = Ride.objects.get(id=booking.ride_id)
                                    ride.available_seats -= 1
                                    ride.save()
                                    return JsonResponse({"success": True})
                                else:
                                    booking.delete()
                                    return JsonResponse({"success": False, "error": "Payment failed. Please try again."})

                            messages.success(request, "Ride booked successfully!")
                        except Exception as e:
                            print(f"Failed at transaction creation: {str(e)}")
                            messages.error(request, f"Failed at transaction creation: {str(e)}")
                            booking.delete()  # Rollback on failure
                    else:
                        messages.error(request, "Payment failed. Please try again.")
                        booking.delete()  # Rollback on failure

            except stripe.error.StripeError as e:
                print(f"Payment error: {str(e)}")
                messages.error(request, f"Payment error: {str(e)}")
                booking.delete()  # Rollback on failure
            except Exception as e:
                print(f"Something went wrong: {str(e)}")
                messages.error(request, f"Something went wrong: {str(e)}")
                booking.delete()  # Rollback on failure
    return redirect("book_ride")


def calculate_fare(request):
    try:
        pickup_lat = float(request.GET.get("pickup_lat"))
        pickup_lon = float(request.GET.get("pickup_lon"))
        dropoff_lat = float(request.GET.get("dropoff_lat"))
        dropoff_lon = float(request.GET.get("dropoff_lon"))

        # Calculate distance (in km)
        distance_miles = geodesic((pickup_lat, pickup_lon), (dropoff_lat, dropoff_lon)).miles

        # Example: Base fare $5 + $3 per mile
        fare = 5 + (distance_miles * 3)

        return JsonResponse({"fare": round(fare, 2)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

from django.shortcuts import render
from django.utils.timezone import now

def get_my_rides(request):
    user = request.user
    current_time = timezone.now()

    created_rides = Ride.objects.filter(driver=user)
    booked_rides = BookedRide.objects.filter(user=user).select_related('ride')

    def categorize_rides(rides, is_booked=False):
        upcoming = []
        ongoing = []
        completed = []

        for ride in rides:
            ride_obj = ride if not is_booked else ride.ride
            ride_date_time = ride_obj.date_time

            ride_data = {
                "id": ride_obj.id,
                "pickup_location": ride_obj.pickup_location,
                "dropoff_location": ride_obj.dropoff_location,
                "date_time": ride_date_time.strftime("%Y-%m-%d %H:%M"),
                "available_seats": ride_obj.available_seats,
                "price": str(ride_obj.price) if ride_obj.price else None,
                "vehicle_details": ride_obj.vehicle_details,
            }
            ride_data["can_start"] =  True if (ride_date_time - now()).total_seconds() < 72000  else False

            if is_booked:
                ride_data["fare"] = str(ride.fare) if ride.fare else None
                pickup = json.loads(ride.pickup_location)
                dropoff = json.loads(ride.dropoff_location)
                ride_data["pickup_location"]= str(pickup.get("name", "Unknown Location"))
                ride_data["dropoff_location"] = str(dropoff.get("name", "Unknown Location"))
                ride_data["date_time"] = ride.booked_at.strftime("%Y-%m-%d %H:%M")

            if ride_date_time > current_time:
                upcoming.append(ride_data)
            elif (current_time - ride_date_time).total_seconds() <= 7200:
                ongoing.append(ride_data)
            else:
                completed.append(ride_data)

        return {"upcoming": upcoming, "ongoing": ongoing, "completed": completed}

    context = {
        "created_rides": categorize_rides(created_rides),
        "booked_rides": categorize_rides(booked_rides, is_booked=True),
    }

    return render(request, "MyRides.html", context)

def get_booked_rides(request):
    user = request.user
    booked_rides = BookedRide.objects.filter(user=user).select_related('ride')

    return booked_rides

def cancelBooking(request, ride_id):
    print(ride_id)
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            booking_id = body.get("booking_id")

            if not booking_id:
                return JsonResponse({"success": False, "error": "Booking ID missing"}, status=400)

            # Ensure the booking exists before deleting
            booking = get_object_or_404(BookedRide, id=booking_id)
            
            booking.delete()  # ✅ Correct deletion

            return JsonResponse({"success": True, "message": "Booking canceled successfully"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)

def ride_view(request, ride_id):
    ride = Ride.objects.get(id=ride_id)
    
    # Ensure pickup_metadata and dropoff_metadata are in dictionary format
    pickup_data = ride.pickup_metadata if isinstance(ride.pickup_metadata, dict) else json.loads(ride.pickup_metadata)
    dropoff_data = ride.dropoff_metadata if isinstance(ride.dropoff_metadata, dict) else json.loads(ride.dropoff_metadata)
    try:
        ride.date_time = now()
        ride.save()
    except:
        print('Error starting the ride')

    context = {
        "ride": ride,
        "pickup_lat": pickup_data.get("lat", ""),
        "pickup_lon": pickup_data.get("lon", ""),
        "pickup_display": pickup_data.get("name", pickup_data.get("display_name", "Unknown Pickup")),
        "dropoff_lat": dropoff_data.get("lat", ""),
        "dropoff_lon": dropoff_data.get("lon", ""),
        "dropoff_display": dropoff_data.get("name", dropoff_data.get("display_name", "Unknown Dropoff")),
    }
    return render(request, "RideView.html", context)

@csrf_exempt
def send_notification(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message")
            ride_id = data.get("ride_id")

            if not message or not ride_id:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            booked_rides = BookedRide.objects.filter(ride_id=ride_id)
            recipient_list = [ride.user.email for ride in booked_rides if ride.user.email]

            if not recipient_list:
                return JsonResponse({"error": "No recipients found"}, status=404)

            send_mail(
                subject=f"Ride Notification: {ride_id}",
                message=f"Dear Customer,\n\n{message}\n\nBest regards,\nRide Share Team",
                from_email="testrideshare00@gmail.com",
                recipient_list=recipient_list,
                fail_silently=False,
            )

            return JsonResponse({"success": "Email sent successfully!"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)