from datetime import timedelta
from django.db import models
from django.utils.timezone import now
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Avg 


#        ADMIN MODEL
class Admin(models.Model):
    username = models.CharField(max_length=150, unique=True, default="admin")
    password = models.CharField(max_length=255)  # Stores plain-text password (not recommended)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

#         LOGIN MODEL
class Login(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)  # Storing in plaintext
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    types = models.CharField(
        max_length=50,
        choices=[('admin', 'Admin'), ('user', 'User'), ('employee', 'Employee')],
        default='user'
    )
    status = models.BooleanField(default=True)  # Active status

    def __str__(self):
        return self.username


#         EMPLOYEE MODEL
class Employee(models.Model):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)  # Unique email for login
    username = models.CharField(max_length=100, unique=True, blank=True)  # ✅ Auto-generated username
    password = models.CharField(max_length=255)  # ❌ Plaintext password (Not Secure)
    contact_number = models.CharField(max_length=15, default="0000000000")
    position = models.CharField(max_length=150, default="Employee")
    joined_at = models.DateTimeField(default=now)  # Auto-fill joining date
    status = models.BooleanField(default=True)  # Active status
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.username:  # Only generate username if it's empty
            base_username = slugify(self.name)  # Convert name to lowercase & hyphen-separated
            counter = 1
            unique_username = base_username
            while Employee.objects.filter(username=unique_username).exists():
                unique_username = f"{base_username}{counter}"
                counter += 1
            self.username = unique_username

        super().save(*args, **kwargs)  # Save the model

    def __str__(self):
        return f"{self.name} ({self.email})"

class UserProfile(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected'),
    ]

    user = models.OneToOneField(Login, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=255)  # ⚠️ Stores passwords as plain text
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)  # Default is Pending

    def __str__(self):
        return f"{self.full_name} - {self.get_status_display()}"


#        PRODUCT MODEL

class Product(models.Model):
    AVAILABILITY_CHOICES = [
        ("available", "Available"),
        ("rented", "Rented"),
        ("returned", "Returned"),
        ("damaged", "Damaged"),
        ("pending", "Pending Approval"),
    ]

    CATEGORY_CHOICES = [
        ('casual', 'Casual'),
        ('formal', 'Formal'),
        ('party', 'Party Wear'),
        ('traditional', 'Traditional'),
        ('sportswear', 'Sportswear'),
        ('winter', 'Winter Wear'),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    SIZE_CHOICES = [
    ("S", "Small"),
    ("M", "Medium"),
    ("L", "Large"),
    ("XL", "Extra Large"),
    ("XXL", "Double Extra Large"),
]


    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="casual")  # ✅ Fixed
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="available")
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, default="M")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})" 
    
#       WISHLIST
class Wishlist(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

#       CART
# Function to set the default rental end date
def default_rental_end_date():
    return now() + timedelta(days=7)

class Cart(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, choices=Product.SIZE_CHOICES, default="M")  # ✅ Added size
    quantity = models.PositiveIntegerField(default=1)
    rental_start_date = models.DateField(default=now)
    rental_end_date = models.DateField(default=default_rental_end_date)
    added_at = models.DateTimeField(auto_now_add=True)


#           RENTAL MODEL
class Rental(models.Model):
    customer = models.ForeignKey(Login, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10, 
        choices=Product.AVAILABILITY_CHOICES, 
        default="rented"
    )
    rented_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} rented {self.product.name}"


#          BOOKING MODEL
# Function to set the default rental end date
def default_rental_end_date():
    return now() + timedelta(days=7)

class Booking(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, choices=Product.SIZE_CHOICES, default="M")
    quantity = models.PositiveIntegerField(default=1)
    rental_start_date = models.DateField(default=now)
    rental_end_date = models.DateField(default=default_rental_end_date)
    rental_duration = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)  # New field
    damage_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # New field
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # New field
    refund_status = models.CharField(max_length=20, choices=[
        ("Pending", "Pending"),
        ("Refunded", "Refunded"),
        ("Deducted", "Deducted"),
    ], default="Pending")
    status = models.CharField(max_length=20, choices=[
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Completed", "Completed"),
        ("Canceled", "Canceled"),
    ], default="Pending")
    address = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.rental_duration = (self.rental_end_date - self.rental_start_date).days
        self.total_price = self.product.price * self.quantity * self.rental_duration
        super().save(*args, **kwargs)

    def calculate_final_refund(self):
        """Calculate the refundable amount after deductions."""
        return self.security_deposit - (self.damage_fee + self.late_fee)

    def process_refund(self):
        """Finalize refund based on deductions."""
        final_refund = self.calculate_final_refund()
        self.refund_status = "Refunded" if final_refund > 0 else "Deducted"
        self.save()
        return final_refund



#      PAYMENT MODEL
class Payment(models.Model):
    PAYMENT_METHODS = [
        ("Credit Card", "Credit Card"),
        ("Debit Card", "Debit Card"),
        ("PayPal", "PayPal"),
        ("UPI", "UPI"),
        ("Bank Transfer", "Bank Transfer"),
        ("Razorpay", "Razorpay"),  # Added Razorpay as an option
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Successful", "Successful"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),  # Added refund status
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)  
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Includes security deposit
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)  # New field
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Tracks refunded amount
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # New field
    razorpay_payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # New field
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    payment_date = models.DateTimeField(default=now)

    def process_refund(self, refund_amount):
        """Update refund details when admin processes a refund."""
        self.refund_amount = refund_amount
        self.status = "Refunded"
        self.save()

    def __str__(self):
        return f"Payment for {self.booking.user.username} - {self.amount} ({self.status})"
    

#      FEEDBACK MODEL
class Feedback(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.username}"


#      COMPLAINT MODEL
class Complaint(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    complaint_text = models.TextField()
    status = models.CharField(
        max_length=20, 
        choices=[("Pending", "Pending"), ("Resolved", "Resolved")],
        default="Pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)  # Track resolution time

    def __str__(self):
        return f"Complaint by {self.user.username} - {self.status}"
    

class ChatbotResponse(models.Model):
    question = models.TextField()
    response = models.TextField()  # Stores the chatbot's response
    is_escalated = models.BooleanField(default=False)  # Escalate to admin if not found
    created_at = models.DateTimeField(default=now)  # Keep only this

    def __str__(self):
        return f"Chatbot Response for: {self.question[:50]}..."

#  SALESREPORT    
class SalesReport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    date = models.DateField()
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2)
    report_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.report_status} ({self.total_sales}$)"


