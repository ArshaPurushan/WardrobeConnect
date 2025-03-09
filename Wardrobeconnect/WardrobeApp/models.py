from datetime import timedelta
from django.db import models
from django.utils.timezone import now
from django.utils.text import slugify


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
    profile_picture = models.ImageField(upload_to="employee_images/")

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

#      USER PROFILE MODEL
class UserProfile(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected'),
    ]
    logid = models.OneToOneField('Login', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="Unnamed User")
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)  # Default is Pending

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"  # Display status name



#        PRODUCT MODEL
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    AVAILABILITY_CHOICES = [
        ("available", "Available"),
        ("rented", "Rented"),
        ("returned", "Returned"),
        ("damaged", "Damaged"),
        ("pending", "Pending Approval"),
    ]

    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    description = models.TextField(default="No description available")
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    availability = models.CharField(max_length=10, choices=AVAILABILITY_CHOICES, default="available")

    def __str__(self):
        return self.name


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
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Completed", "Completed"),
        ("Canceled", "Canceled"),
    ]

    user = models.ForeignKey("Login", on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    rental_duration = models.PositiveIntegerField(default=7)  # Duration in days
    rental_start_date = models.DateTimeField(default=now)
    rental_end_date = models.DateTimeField(default=default_rental_end_date)  # ✅ Fixed lambda issue
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # ✅ Added default
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    def save(self, *args, **kwargs):
        """Ensure rental_end_date and total_price are correctly calculated before saving."""
        self.rental_end_date = self.rental_start_date + timedelta(days=self.rental_duration)
        
        # Ensure total_price calculation is safe
        product_price = getattr(self.product, "price", 0)  # Get price safely
        self.total_price = round(product_price * self.quantity * self.rental_duration, 2)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking by {self.user.username} - {self.product.name} ({self.status})"
    
    
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
