from django.urls import path
from .views import plan_ride, bookRideById, get_available_rides, bookRide, calculate_fare, get_rides_by_id,get_my_rides, get_booked_rides, ride_view, cancelBooking, send_notification

urlpatterns = [
    path('plan-ride/', plan_ride, name='plan_ride'),
    path('book-ride/', bookRide, name='book_ride'),
    path('book-ride/<int:ride_id>/cancel-booking/', cancelBooking, name='cancel-booking'),
    path('book-ride/<int:ride_id>/', bookRideById, name='book_ride_by_id'),
    path('ride-start/<int:ride_id>/', ride_view, name='ride_start'),
    path('calculate-fare/', calculate_fare, name='calculate_fare'),
    path('get-rides/', get_available_rides, name='get-rides'),
    path('send-notification/', send_notification, name='send_notification'),
    path('get-my-rides/', get_my_rides, name='get-my-rides'),
    path('get-ride-details/<int:ride_id>/', get_rides_by_id, name='get-rides-by-id'),
]
