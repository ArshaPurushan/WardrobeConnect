from datetime import timedelta
from django.db import models
from django.utils.timezone import now
from django.core.validators import RegexValidator
from django.core.exceptions import ObjectDoesNotExist

# ADMIN MODEL
class Admin(models.Model):
    username = models.CharField(max_length=150, unique=True, default="admin")
    password = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    
    def __str__(self):
        return self.username

# LOGIN MODEL (Custom User Authentication)
class Login(models.Model):
    email = models.EmailField(unique=True, null=False, blank=False)
    password = models.CharField(max_length=255)
    types = models.IntegerField(
        choices=[(0, 'Admin'), (1, 'User'), (2, 'Employee')],
        default=1
    )
    status = models.BooleanField(default=True)
    last_login = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.email

# USER PROFILE MODEL
class UserProfile(models.Model):
    STATUS_CHOICES = [
        (0, 'Active'),
        (1, 'Reported'),
        (2, 'Blocked'),
    ]

    user = models.OneToOneField(Login, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Invalid phone format")
    phone = models.CharField(max_length=15, unique=True, validators=[phone_regex])
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    profile_picture = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.get_status_display()}"

# EMPLOYEE MODEL
class Employee(models.Model):
    user = models.OneToOneField(Login, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50, default="Unknown Employee")
    position = models.CharField(
        max_length=150,
        choices=[
            ("0", "General Staff"),
            ("1", "Manager"),
            ("2", "Delivery Staff")
            
        ],
        default="General Staff"
    )
    joined_at = models.DateTimeField(default=now)
    profile_picture = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.position})"

# PRODUCT MODEL
from django.utils import timezone
class Product(models.Model):
    AVAILABILITY_CHOICES = [
        (0, "Available"),
        (1, "Rented"),
        (2, "Returned"),
        (3, "Damaged"),
        (4, "Pending Approval"),
    ]
    CATEGORY_CHOICES = [
        (0, 'Clothing'), (1, 'Accessories'), (2, 'Footwear')
    ]
    SUBCATEGORY_CHOICES = [
        (0, 'Casual'), (1, 'Formal'), (2, 'Party Wear'),
        (3, 'Traditional'), (4, 'Sportswear'), (5, 'Winter Wear'),
        (6, 'Jewelry'), (7, 'Watches'), (8, 'Bags'), (9, 'Shoes')
    ]
    GENDER_CHOICES = [(0, 'Male'), (1, 'Female'), (2, 'Unisex'), (3, 'Boys'), (4, 'Girls')]
    VERIFICATION_CHOICES = [(0, 'Pending'), (1, 'Verified')]


    name = models.CharField(max_length=255)
    category = models.IntegerField(choices=CATEGORY_CHOICES, default=0)
    subcategory = models.IntegerField(choices=SUBCATEGORY_CHOICES, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)
    availability = models.IntegerField(choices=AVAILABILITY_CHOICES, default=0)
    gender = models.IntegerField(choices=GENDER_CHOICES, default=2)
    added_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    size_stock = models.JSONField(default=dict)  # Added stock field ✅
    is_verified = models.IntegerField(choices=VERIFICATION_CHOICES, default=0)  # Admin verification ✅
    created_at = models.DateTimeField(default=timezone.now) 
    
    def total_stock(self):
        """
        Returns the total stock for all sizes of this product.
        """
        total = 0
        for size in self.sizes.all():  # Assuming there's a reverse relationship 'sizes' for ProductSize
            total += size.stock  # Assuming 'stock' is a field in ProductSize model
        return total
        #return sum(self.size_stock.values()) if self.size_stock else 0
        

    def remove_if_damaged(self):
        if self.availability == 3:  # Damaged
            self.delete()

    def __str__(self):
        return f"{self.name} ({self.get_subcategory_display()})"


# PRODUCT SIZE MODEL
class ProductSize(models.Model):
    SIZE_CHOICES = [
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
        ("XXL", "XX-Large"),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=5, choices=SIZE_CHOICES)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} - {self.get_size_display()}"

    def is_available(self, rental_start_date, rental_end_date, quantity=1):
        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            product_size=self,
            is_active=True,
            booked_at__lte=rental_end_date,
            return_by__gte=rental_start_date
        )
        
        # Calculate the total quantity booked in the overlapping period
        booked_quantity = sum(booking.quantity for booking in overlapping_bookings)
        
        # Actual available stock
        available_stock = self.stock - booked_quantity
        
        # Return whether there's enough stock for the requested quantity
        return available_stock >= quantity

# CART MODEL
class Cart(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)  # Link to customer 
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)  # Store product size selection
    quantity = models.PositiveIntegerField(default=1)  # Users can rent multiple of the same product
    added_at = models.DateTimeField(auto_now_add=True)  # Track when added

    def __str__(self):
        return f"{self.user.email} - {self.product_size.product.name} (Qty: {self.quantity})"

    def total_price(self):
        """Calculate total price of items in the cart."""
        return self.quantity * self.product_size.product.price

    def update_quantity(self, new_quantity):
        """Update the quantity of the product in the cart."""
        if new_quantity <= self.product_size.stock:  # Ensure stock is available
            self.quantity = new_quantity
            self.save()
        else:
            raise ValueError("Insufficient stock to update the quantity.")
    
    def remove_product(self):
        """Remove product from the cart."""
        self.delete()

    def available_stock(self):
        """Check if the required quantity is available in stock."""
        return self.product_size.stock >= self.quantity

    def save(self, *args, **kwargs):
        """Override save method to ensure availability check."""
        if not self.available_stock():
            raise ValueError("Not enough stock available for the selected quantity.")
        super().save(*args, **kwargs)
        
# WISHLIST MODEL
class Wishlist(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)  # Link to customer
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Store only product (size not needed)
    added_at = models.DateTimeField(auto_now_add=True)  # Track when added

    def __str__(self):
        return f"{self.user.email} - {self.product.name} (Wishlist)"



# BOOKING MODEL
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta
from django.utils.timezone import now

# Helper function for the default rental end date (7 days after booking)
def default_rental_end_date():
    return now() + timedelta(days=7)

class Booking(models.Model):
    customer = models.ForeignKey('Login', on_delete=models.CASCADE)
    product_size = models.ForeignKey('ProductSize', on_delete=models.CASCADE, null=True, blank=True)
    assigned_employee = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True)

    # Status choices for booking
    STATUS_CHOICES = [
        (1, "Pending"),
        (2, "Confirmed"),
        (3, "Completed"),  # Booking completed (and can be refunded)
        (4, "Cancelled"),   # Booking cancelled (refund rejected)
    ]

    TRACKING_CHOICES = [
        ("placed", "Order Placed"),
        ("processing", "Processing Started"),
        ("packed", "Packed"),
        ("ready_for_pickup", "Ready for Pickup"),
        ("delivered", "Handed Over to Customer"),
        ("returned", "Returned to Store"),
        ("refunded", "Refund Processed"),
    ]

        # Refund status choices
    REFUND_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Refund Process Initiated '),
        ('processed', 'Refund Completed'),
        ('rejected', 'Rejected'),
    ]

    refund_status = models.CharField(max_length=10, choices=REFUND_CHOICES, default='pending')

    # Booking status and tracking status fields
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=1)
    tracking_status = models.CharField(max_length=30, choices=TRACKING_CHOICES, default="placed")

    # Booking details
    is_active = models.BooleanField(default=True)  # Indicates whether the booking is active or not
    booked_at = models.DateTimeField(default=now)  # Booking creation timestamp
    return_by = models.DateTimeField(default=now)  # Rental return deadline
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Security deposit amount
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total rental price

    # Customer information for the booking
    booking_name = models.CharField(max_length=255, blank=True, null=True)
    booking_address = models.TextField(null=True, blank=True)
    booking_phone = models.CharField(max_length=15, blank=True)

    # Employee who updated the tracking status
    tracking_updated_by = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tracking_updates"
    )

    # Refund-related fields
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Late fee, if any
    inspection_note = models.TextField(null=True, blank=True)  # Notes from employee during inspection

    def save(self, *args, **kwargs):
        """Ensure proper defaults for return_by and product_size before saving."""
        if not self.return_by:
            self.return_by = self.booked_at + timedelta(days=7)
        
        if not self.product_size:  
            try:
                self.product_size = ProductSize.objects.first()
            except ObjectDoesNotExist:
                print("Warning: No ProductSize exists. Booking saved without a product size.")
        
        super().save(*args, **kwargs)

    def complete_booking(self):
        """Mark booking as completed."""
        self.is_active = False  # Booking is no longer active
        self.status = 3  # Status: Completed
        self.save()

    def process_refund(self, refund_status, late_fee=None, inspection_note=None):
        """
        Process the refund and update the booking status and tracking info.
        """
        # Validate and apply the refund status
        if refund_status == "approved":  # "Refund Process Initiated" by employee
            self.status = 2  # Optionally a custom status to represent intermediate step
            self.tracking_status = "refund_initiated"
        elif refund_status == "processed":  # "Refund Completed" by admin
            self.status = 3  # Completed
            self.tracking_status = "refunded"
        elif refund_status == "rejected":
            self.status = 4  # Cancelled
            self.tracking_status = "rejected"
        elif refund_status == "pending":
            self.status = 1  # Pending
        else:
            raise ValueError("Invalid refund status.")

        # Set the refund_status field
        self.refund_status = refund_status

        # Handle the late fee
        if late_fee is not None:
            try:
                self.late_fee = float(late_fee)
            except ValueError:
                raise ValueError("Invalid late fee value.")

        # Add inspection note if any
        if inspection_note:
            self.inspection_note = inspection_note

        # Save the changes
        self.save()


# RENTED MODE;
class Rental(models.Model):
    STATUS_CHOICES = [
        (1, "Rented"),
        (2, "Returned"),
        (3, "Overdue"),
    ]
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Login, on_delete=models.CASCADE)
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, null=True, blank=True)
    rented_at = models.DateTimeField(auto_now_add=True)
    return_by = models.DateTimeField(default=default_rental_end_date)
    is_active = models.BooleanField(default=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=1)

    def mark_returned(self):
        self.is_active = False
        self.save()
        self.booking.complete_booking()  # Update booking status as well

    def __str__(self):
        return f"{self.customer.email} - {self.product_size.product.name} (Active: {self.is_active})"


# RETURN MODEL
class Return(models.Model):
    CONDITION_CHOICES = [
        ("Good", "Good"),
        ("Damaged", "Damaged"),
        ("Needs Cleaning", "Needs Cleaning"),
    ]
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    returned_at = models.DateTimeField(auto_now_add=True)
    condition = models.CharField(max_length=255, choices=CONDITION_CHOICES, default="Good")
    handled_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    #refund_status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("confirmed", "Confirmed"), ("rejected", "Rejected")], default="pending")
    employee_note = models.TextField(blank=True, null=True)
    
                   
def save(self, *args, **kwargs):
    """Override save to handle the comparison between returned_at and return_by."""
    
    # Ensure both 'returned_at' and 'return_by' are not None before comparing
    if self.returned_at and self.booking.return_by:
        if self.returned_at > self.booking.return_by:
            raise ValueError("Returned date cannot be after the booking return date.")
    
    super().save(*args, **kwargs)


# PAYMENT MODEL
class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit_refunded = models.BooleanField(default=False)
    payment_method = models.IntegerField(choices=[(0, "Credit Card"), (1, "UPI")])
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.IntegerField(choices=[(0, "Pending"), (1, "Successful"), (2, "Failed")], default=0)
    payment_date = models.DateTimeField(default=now)
    
    def refund_security_deposit(self):
        if self.booking.return_set.exists() and not self.security_deposit_refunded:
            self.amount -= self.booking.return_set.first().late_fee
            self.security_deposit_refunded = True
            self.save()
    
    def process_refund(self, admin_approval=False):
        """Manually process security deposit refunds."""
        if admin_approval:
            self.security_deposit_refunded = True
            self.amount -= self.booking.return_set.first().late_fee if self.booking.return_set.exists() else 0
            self.save()
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.get_status_display()}"
    
# FEEDBACK MODEL
class Feedback(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    rating = models.IntegerField(choices=[(i, f"{i} Star") for i in range(1, 6)], default=5)  # Rating field added
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.email}"
    
# COMPLAINT MODEL
class Complaint(models.Model):
    STATUS_CHOICES = [(0, "Pending"), (1, "Resolved"), (2, "Rejected")]

    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    admin_response = models.TextField(null=True, blank=True) 

    def __str__(self):
        return f"Complaint by {self.user.email} - {self.get_status_display()}"

# REVIEW MODEL
class ProductReview(models.Model):
    user = models.ForeignKey(Login, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)  # Scale of 1-5
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐ by {self.user.email}"
    
# CHATBOT MODEL
class ChatbotQuery(models.Model):
    user = models.ForeignKey(Login, on_delete=models.SET_NULL, null=True, blank=True)
    query = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Query by {self.user.email if self.user else 'Guest'} at {self.timestamp}"


class ProductRecommendation(models.Model):
    RECOMMENDATION_TYPE_CHOICES = [
        ('accessory', 'Accessory'),
        ('complementary', 'Complementary Item'),
        ('matching', 'Matching Item'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recommended_for")
    recommended_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recommended_products")
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE_CHOICES, default="accessory")

    class Meta:
        unique_together = ('product', 'recommended_product', 'recommendation_type')

    
    def __str__(self):
        return f"{self.recommended_product.name} ({self.get_recommendation_type_display()}) recommended for {self.product.name}"
    
# REPORT MODEL
from django.utils import timezone

class Report(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="reports")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)  # Make it optional, we will generate it later
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    #verified_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_reports")

    # Fields for the report details
    items_added = models.IntegerField(default=0)  # Number of products added
    bookings_made = models.IntegerField(default=0)  # Number of bookings made

    def __str__(self):
        return f"Report: {self.title} by {self.employee.name}"

    def generate_daily_activity_data(self):
        """
        Populates the daily activity data (number of items added, bookings made).
        Also generates a description for the report.
        """
        today = timezone.now().date()

        # Count the number of products added today
        self.items_added = Product.objects.filter(created_at__date=today).count()

        # Count the number of bookings made today
        self.bookings_made = Booking.objects.filter(booked_at__date=today).count()

        # Create a description for the report based on the counts
        self.description = f"Added {self.items_added} new products to the inventory. " \
                           f"{self.bookings_made} bookings were made today."

        self.save()  # Save the report after generating data