from django.db import models
from users.models import CustomUser

class Ride(models.Model):
    driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    pickup_metadata = models.JSONField(default=dict)
    dropoff_metadata = models.JSONField(default=dict)
    vehicle_details = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    available_seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)    

    def __str__(self):
        return f"{self.pickup_location} to {self.dropoff_location}"

class BookedRide(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ride = models.ForeignKey('Ride', on_delete=models.CASCADE)
    pickup_location = models.JSONField()  # Store metadata
    dropoff_location = models.JSONField()
    fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking by {self.user.email} - {self.ride}"

class Transaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ride = models.ForeignKey('BookedRide', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Fare amount
    status = models.CharField(max_length=20, choices=[('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')])
    stripe_payment_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.id} - {self.status}"