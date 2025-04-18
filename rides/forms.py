from django import forms
from django.utils.timezone import is_naive, make_aware
import pytz
from .models import Ride, BookedRide

class PlanRideForm(forms.ModelForm):
    pickup_metadata = forms.JSONField(widget=forms.HiddenInput())  # Hidden field to store JSON
    dropoff_metadata = forms.JSONField(widget=forms.HiddenInput())

    class Meta:
        model = Ride
        fields = ['pickup_location', 'dropoff_location', 'pickup_metadata', 'dropoff_metadata',
                  'vehicle_details', 'date_time', 'available_seats', 'price']
        widgets = {
            'pickup_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter pickup location'}),
            'dropoff_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter dropoff location'}),
            'vehicle_details': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vehicle brand & seating capacity'}),
            'date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'available_seats': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter number of vacant seats'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price per seat'}),
        }
    def clean_date_time(self):
        date_time = self.cleaned_data['date_time']
        if is_naive(date_time):
            return make_aware(date_time, timezone=pytz.UTC)
        return date_time
    

class BookRideForm(forms.ModelForm):
    pickup_location = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter or detect pickup location'}),
        required=True
    )
    dropoff_location = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter dropoff location'}),
        required=True
    )
    fare = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        required=True
    )

    class Meta:
        model = BookedRide
        fields = ['pickup_location', 'dropoff_location', 'fare']

    def __init__(self, *args, **kwargs):
        self.ride = kwargs.pop('ride', None)  # Pass ride object to form
        super().__init__(*args, **kwargs)

    # def calculate_fare(self, pickup_lat, pickup_lon, dropoff_lat, dropoff_lon):
    #     """Calculate fare based on distance using the stored ride price."""
    #     import geopy.distance
    #     try:
    #         start = (pickup_lat, pickup_lon)
    #         end = (dropoff_lat, dropoff_lon)
    #         distance_km = geopy.distance.geodesic(start, end).km

    #         if self.ride:
    #             base_price = self.ride.price
    #             fare = round(base_price * (distance_km / self.ride.distance_km), 2)  # Adjust pricing dynamically
    #             return fare
    #     except Exception as e:
    #         print("Error calculating fare:", e)
    #         return None
        