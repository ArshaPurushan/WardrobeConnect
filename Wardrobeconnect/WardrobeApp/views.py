import io
import os
import razorpay
import pandas as pd
from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse  
from razorpay.errors import BadRequestError, ServerError, SignatureVerificationError
from django.db import IntegrityError
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from datetime import datetime
import random
from django.conf import settings
from django.db.models import Q
from django.template.loader import get_template
from django.urls import reverse
from django.db import transaction
from .forms import EmployeeForm
from .forms import ProductForm
from .forms import ProfileUpdateForm, ProductReviewForm
from .models import Login, UserProfile, Admin, Employee
from .models import Product, ProductSize, Rental, Payment, Booking, Return
from .models import Complaint, Report, Cart, Wishlist, Feedback
from .models import ChatbotQuery, ProductRecommendation
from django.contrib.auth.decorators import login_required

# ==============================
#         HOME PAGE
# ==============================
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


# ==============================
#       LOGIN
# ==============================


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        print(f"🛠️ Debug: Email entered: {email}, Password entered: {password}")

        if not email or not password:
            messages.error(request, "Both email and password are required!")
            return redirect("login")

        user = None  # Initialize user as None

        # ✅ Check if the user exists in the Login table (Customers & Employees)
        try:
            user = Login.objects.get(email__iexact=email)
        except Login.DoesNotExist:
            pass  # Move to check Admin table

        # ✅ If not found in Login, check the Admin table
        if user is None:
            try:
                user = Admin.objects.get(email__iexact=email)
                is_admin = True  # Flag to indicate this is an admin
            except Admin.DoesNotExist:
                print("❌ Debug: No user found in either Login or Admin table!")
                messages.error(request, "Invalid email or password.")
                return redirect("login")
        else:
            is_admin = False  # This is a regular user (not an admin)

        print(f"✅ Debug: User found - {user.email}, Stored password: {user.password}")

        # ⚠️ Plain-Text Password Check (No Hashing)
        if user.password != password:
            print("❌ Debug: Password does not match!")
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        # ✅ Set session variables
        request.session["id"] = user.id
        request.session["email"] = user.email
        request.session["user_type"] = "0" if is_admin else str(user.types)

        # ✅ Admin Login
        if is_admin:
            messages.success(request, "Admin login successful!")
            return redirect("admin_dashboard")

        # ✅ Customer Login
        if user.types == 1:
            profile = UserProfile.objects.filter(user=user).first()
            if not profile:
                messages.error(request, "User profile not found.")
                return redirect("login")
            
            if profile.status == 1:
                messages.error(request, "Your account has been reported and is under review.")
                return redirect("login")
            elif profile.status == 2:
                messages.error(request, "Your account has been blocked.")
                return redirect("login")

            messages.success(request, "Customer login successful!")
            return redirect("customer_dashboard")

        # ✅ Employee Login
        if user.types == 2:
            employee = Employee.objects.filter(user=user).first()
            if not employee:
                messages.error(request, "Employee profile not found.")
                return redirect("login")

            messages.success(request, "Employee login successful!")
            return redirect("employee_dashboard")

    return render(request, "login.html")

# ==============================
#       LOGOUT
# ==============================
def logout_view(request):
    return render(request, 'logout.html') 


# ==============================
#         USER REGISTRATION
# ==============================

def register(request):
    if request.method == "POST":
        print(request.POST)  # Debugging: Print POST data

        # Extract and clean input data
        name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # Input validation
        errors = []
        
        # Validate required fields
        if not name:
            errors.append("Name is required.")
        if not phone:
            errors.append("Phone number is required.")
        if not email:
            errors.append("Email is required.")
        if not password:
            errors.append("Password is required.")
        if not confirm_password:
            errors.append("Confirm password is required.")

        # Validate email format
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        
        # Check for existing email
        if Login.objects.filter(email=email).exists():
            errors.append("Email already exists.")
        
        # Password validation
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # If there are validation errors, return with messages
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "register.html", {
                'full_name': name,
                'phone': phone,
                'email': email
            })

        try:
            with transaction.atomic():  # Ensure atomic transactions
                # Create login instance
                login_instance = Login.objects.create(
                    email=email,
                    password=password,  # Plain text password (NOT SECURE)
                    types=1,  # Ensure this matches the database field type
                    status=True  # Users are active upon registration
                )

                # Create user profile
                UserProfile.objects.create(
                    user=login_instance, 
                    full_name=name, 
                    phone=phone
                )

            messages.success(request, "Registration successful! Please log in.")
            return redirect("login")

        except Exception as e:
            print(f"Registration error: {str(e)}")  # Debugging
            messages.error(request, "An unexpected error occurred. Please try again.")
            return redirect("register")

    return render(request, "register.html")

# ==============================
#         USER MANGEMENT(ADMIN
# ==============================

def is_admin(user):
    return user.is_authenticated and user.is_staff  # Ensure only admins can access

def manage_users(request, status="active"):
    """View to manage users based on their status."""
    
    # if not is_admin(request.user):  # Check if the user is an admin
    #     return redirect("customer_dashboard")  # Redirect non-admin users

    status_mapping = {
        "active": 0,
        "reported": 1,
        "blocked": 2,
    }

    # if status not in status_mapping:
    status = "active"  # Default to active users

    users = UserProfile.objects.filter(status=status_mapping[status])
    
    return render(request, "manage_users.html", {"users": users, "status": status})



def report_user(request, user_id):
    """Mark a user as reported."""
    if not is_admin(request.user):
        return redirect("customer_dashboard")

    user = get_object_or_404(UserProfile, id=user_id)

    if user.status == 1:
        messages.info(request, f"User '{user.full_name}' is already reported.")
    else:
        user.status = 1  # Mark as reported
        user.save()
        messages.warning(request, f"User '{user.full_name}' has been reported.")

    return redirect("manage_users_with_status", status="active")

def block_user(request, user_id):
    """Block a user."""
    if not is_admin(request.user):
        return redirect("customer_dashboard")

    user = get_object_or_404(UserProfile, id=user_id)

    if user.status == 2:
        messages.info(request, f"User '{user.full_name}' is already blocked.")
    else:
        user.status = 2  # Block user
        user.save()
        messages.error(request, f"User '{user.full_name}' has been blocked.")

    return redirect("manage_users_with_status", status="active")

def activate_user(request, user_id):
    """Reactivate a user from reported or blocked status."""
    if not is_admin(request.user):
        return redirect("customer_dashboard")

    user = get_object_or_404(UserProfile, id=user_id)

    if user.status == 0:
        messages.info(request, f"User '{user.full_name}' is already active.")
    else:
        user.status = 0  # Reactivate user
        user.save()
        messages.success(request, f"User '{user.full_name}' has been reactivated.")

    return redirect("manage_users_with_status", status="reported" if user.status == 1 else "blocked")

# ==============================
#         EMPLOYEE MANGEMENT(ADMIN
# ==============================
def manage_employees(request):
    employees = Employee.objects.all()
    return render(request, 'manage_employees.html', {'employees': employees})

def add_employee(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES)  # Handle profile picture upload
        if form.is_valid():
            form.save()
            messages.success(request, "New employee added successfully!")
            return redirect('manage_employees')
        else:
            messages.error(request, "Error adding employee. Please check the form.")
    else:
        form = EmployeeForm()
    
    return render(request, 'add_employee.html', {'form': form})

def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee details updated successfully!")
            return redirect('manage_employees')
        else:
            messages.error(request, "Error updating employee details.")
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'edit_employee.html', {'form': form, 'employee': employee})

def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    employee.delete()
    messages.success(request, "Employee deleted successfully!")
    return redirect('manage_employees')



# ==============================
#    DASHBOARD
# ==============================
# Admin Dashboard
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")

# Employee Dashboard
def employee_dashboard(request):
    email = request.session.get("email")
    user_type = request.session.get("user_type")

    if not email or user_type != "2":  # Employee type is "2"
        messages.error(request, "Unauthorized access!")
        return redirect("login")  

    try:
        # Fetch employee using session email (linked via Login model)
        employee = Employee.objects.get(user__email=email)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found!")
        return redirect("login")

    return render(request, "employee_dashboard.html", {"employee": employee})

# Customer Dashboard
def customer_dashboard(request):
    email = request.session.get("email")
    user_type = request.session.get("user_type")

    if not email or user_type != "1":  # Ensure user_type is a string
        messages.error(request, "Unauthorized access!")
        return redirect("login")

    # Fetch user details
    login_instance = get_object_or_404(Login, email=email)
    user_profile = get_object_or_404(UserProfile, user=login_instance)

    # Fetch available products
    products = Product.objects.filter(availability=1)

    # Fetch user's rented items
    rented_products = Rental.objects.filter(customer=user_profile.user, is_active=True)


    # Fetch real-time counts for dynamic updates
    cart_count = Cart.objects.filter(user=user_profile.user).count()
    wishlist_count = Wishlist.objects.filter(user=user_profile.user).count()

    # Handle AJAX request for dynamic updates
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "cart_count": cart_count,
            "wishlist_count": wishlist_count,
        })

    # Normal page render
    context = {
        "user_profile": user_profile,
        "products": products,
        "rented_products": rented_products,
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
    }
    return render(request, "customer_dashboard.html", context)

# ==============================
#    PRODUCT MANAGEMENT (EMPLOYEE)
# ==============================
from django.db.models import Sum
def employee_inventory(request):
    """ Display inventory for employees with optional filtering. """
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied: Only employees can access inventory.")
        return redirect("login")

    email = request.session.get("email")
    try:
        login_instance = Login.objects.get(email=email)
        employee = Employee.objects.get(user=login_instance)
    except (Login.DoesNotExist, Employee.DoesNotExist):
        employee = None
        messages.error(request, "Employee profile not found.")
        return redirect("login")

    products = Product.objects.all()

    # Filter: show only products added by the logged-in employee
    filter_by = request.GET.get('filter_by')
    if filter_by == 'my_products':
        products = products.filter(added_by=employee)

    for product in products:
        product.total_stock = ProductSize.objects.filter(product=product).aggregate(Sum("stock"))["stock__sum"] or 0
        product.available_sizes = list(ProductSize.objects.filter(product=product).values_list("size", flat=True))

    return render(request, "employee_inventory.html", {"products": products, "employee": employee})


def add_product(request):
    """ Allow employees to add a product and its sizes + stock. """
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied.")
        return redirect("login")

    if request.method == "POST":
        email = request.session.get("email")
        try:
            login_instance = Login.objects.get(email=email)
            employee = Employee.objects.get(user=login_instance)
        except (Login.DoesNotExist, Employee.DoesNotExist):
            messages.error(request, "Employee not found.")
            return redirect("login")

        # Step 1: Get product details from the form
        product = Product.objects.create(
            name=request.POST.get('name'),
            category=request.POST.get('category'),
            subcategory=request.POST.get('subcategory'),
            price=request.POST.get('price'),
            description=request.POST.get('description'),
            image=request.FILES.get('image'),
            availability=request.POST.get('availability'),
            gender=request.POST.get('gender'),
            added_by=employee,
        )

        # Step 2: Save stock for each selected size
        sizes = request.POST.getlist('sizes')
        for size in sizes:
            stock = int(request.POST.get(f"stock_{size}", 0))
            ProductSize.objects.create(product=product, size=size, stock=stock)

        messages.success(request, "Product added successfully!")
        return redirect('employee_inventory')

    return render(request, 'employee_add_product.html')


def edit_product(request, product_id):
    """ Edit product details + stock (only by the employee who added it). """
    product = get_object_or_404(Product, id=product_id)

    email = request.session.get("email")
    try:
        login_instance = Login.objects.get(email=email)
        employee = Employee.objects.get(user=login_instance)
    except (Login.DoesNotExist, Employee.DoesNotExist):
        messages.error(request, "Unauthorized.")
        return redirect("login")

    if product.added_by != employee:
        messages.error(request, "You can only edit products you added.")
        return redirect("employee_inventory")

    product_sizes = ProductSize.objects.filter(product=product)
    selected_sizes = [ps.size for ps in product_sizes]

    if request.method == "POST":
        # Update product fields
        product.name = request.POST.get('name')
        product.category = request.POST.get('category')
        product.subcategory = request.POST.get('subcategory')
        product.price = request.POST.get('price')
        product.description = request.POST.get('description')
        product.availability = request.POST.get('availability')
        product.gender = request.POST.get('gender')

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()

        # Update stock for sizes
        sizes = request.POST.getlist('sizes')
        existing = {ps.size: ps for ps in product_sizes}

        for size in sizes:
            stock = int(request.POST.get(f'stock_{size}', 0))
            if size in existing:
                existing[size].stock = stock
                existing[size].save()
            else:
                ProductSize.objects.create(product=product, size=size, stock=stock)

        messages.success(request, "Product updated successfully!")
        return redirect('employee_inventory')

    return render(request, 'employee_edit_product.html', {
        'product': product,
        'product_sizes': product_sizes,
        'selected_sizes': selected_sizes,
    })


def delete_product(request, product_id):
    """ Delete a product if not rented. Only if the employee added it. """
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied.")
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    email = request.session.get("email")
    try:
        employee = Employee.objects.get(user__email=email)
    except Employee.DoesNotExist:
        messages.error(request, "Unauthorized.")
        return redirect("login")

    if product.added_by != employee:
        messages.error(request, "You can only delete products you added.")
        return redirect("employee_inventory")

    if Rental.objects.filter(product_size__product=product, is_active=True).exists():
        messages.error(request, "Cannot delete product that is currently rented.")
        return redirect("employee_inventory")

    if request.method == "POST":
        product.delete()
        messages.success(request, f"Product '{product.name}' deleted successfully!")

    return redirect("employee_inventory")


def update_availability(request, product_id):
    """ Update availability status. """
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied.")
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    email = request.session.get("email")
    try:
        employee = Employee.objects.get(user__email=email)
    except Employee.DoesNotExist:
        messages.error(request, "Unauthorized.")
        return redirect("login")

    if product.added_by != employee:
        messages.error(request, "You can only update products you added.")
        return redirect("employee_inventory")

    if request.method == "POST":
        try:
            availability = int(request.POST.get("availability"))
        except (TypeError, ValueError):
            messages.error(request, "Invalid availability.")
            return redirect("employee_inventory")

        if availability in dict(Product.AVAILABILITY_CHOICES).keys():
            product.availability = availability
            product.save()

            if availability == 3:  # Damaged
                product.remove_if_damaged()
                messages.warning(request, f"Product '{product.name}' marked as damaged.")
            else:
                messages.success(request, f"Availability updated to '{product.get_availability_display()}'.")
        else:
            messages.error(request, "Invalid availability selected.")

    return redirect("employee_inventory")




# ==============================
#    PRODUCT MANAGEMENT (admin)
# ==============================

from django.contrib import messages

def admin_manage_inventory(request):
    products = Product.objects.all()
    pending_products = Product.objects.filter(is_verified=0)  # Fix: Use is_verified instead of status

    if pending_products.exists():
        messages.warning(request, f"There are {pending_products.count()} pending products awaiting approval.")

    for product in products:
        product.is_available = product.total_stock() > 0  # Use total_stock() instead of stock
        product.is_rented = Rental.objects.filter(product_size__in=product.sizes.all(), is_active=True).exists()  # Fix rental tracking

        print(f"Total stock for {product.name}: {product.total_stock()}")
    
    return render(request, 'admin_manage_inventory.html', {'products': products})

def approve_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_verified = 1  # Setting to approved (use is_verified field)
    product.save()
    messages.success(request, f"Product {product.name} has been approved.")
    return redirect('admin_manage_inventory')

def reject_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_verified = 2  # Setting to rejected (use is_verified field)
    product.save()
    messages.error(request, f"Product {product.name} has been rejected.")
    return redirect('admin_manage_inventory')

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Optional: Add any deletion restrictions here (like only delete if not rented)
    if Rental.objects.filter(product_size__in=product.sizes.all(), is_active=True).exists():
        messages.error(request, f"Cannot delete '{product.name}' as it is currently rented.")
        return redirect('admin_manage_inventory')

    product.delete()
    messages.success(request, f"Product '{product.name}' has been deleted.")
    return redirect('admin_manage_inventory')


# ==============================
#    SEARCH PRODUCT
# ==============================

def search(request):
    query = request.GET.get("q", "").strip()  # Search by name or description
    category = request.GET.get("category", "").strip()  # Typed category
    subcategory = request.GET.get("subcategory", "").strip()  # Typed subcategory
    gender = request.GET.get("gender", "")  # Dropdown for gender
    size = request.GET.get("size", "")  # Dropdown for size
    price_min = request.GET.get("price_min", "")  # Min price
    price_max = request.GET.get("price_max", "")  # Max price

    # Start with all available products
    products = Product.objects.filter(availability=0, is_verified="1")

    # Filter by search query (name or description)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Filter by category and subcategory (typed)
    if category:
        products = products.filter(category__icontains=category)
    if subcategory:
        products = products.filter(subcategory__icontains=subcategory)

    # Filter by gender (dropdown)
    if gender:
        products = products.filter(gender=gender)

    # Filter by price range (min and max)
    if price_min.isdigit() and price_max.isdigit():
        products = products.filter(price__gte=int(price_min), price__lte=int(price_max))
    elif price_min.isdigit():
        products = products.filter(price__gte=int(price_min))
    elif price_max.isdigit():
        products = products.filter(price__lte=int(price_max))

    # Filter by size (dropdown)
    if size:
        products = products.filter(sizes__size=size, sizes__stock__gt=0).distinct()

    # Pass products to the template
    context = {
        "products": products,
        "categories": Product.CATEGORY_CHOICES,
        "subcategories": Product.SUBCATEGORY_CHOICES,
        "genders": Product.GENDER_CHOICES,
        "sizes": ProductSize.SIZE_CHOICES,
    }

    return render(request, "search.html", context)

# ==============================
#    PRODUCT DETAILS (Clean)
# ==============================

def product_details(request, product_id):
    # Get the main product
    product = get_object_or_404(Product, id=product_id)

    # Get available sizes that are in stock
    available_sizes = ProductSize.objects.filter(product=product, stock__gt=0)

    # Get all recommended products for this product
    recommendations = ProductRecommendation.objects.filter(product=product).select_related('recommended_product')

    # Only include recommended products that are in stock
    recommended_products = [
        rec.recommended_product
        for rec in recommendations
        if ProductSize.objects.filter(product=rec.recommended_product, stock__gt=0).exists()
    ]

    return render(request, "product_details.html", {
        "product": product,
        "available_sizes": available_sizes,
        "recommended_products": recommended_products,
    })


# ==============================
#    CHECK AVAILABILITY
# ==============================


def check_availability(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        size = request.POST.get("size")
        rental_start_date = request.POST.get("rental_start_date")
        rental_end_date = request.POST.get("rental_end_date")
        quantity = int(request.POST.get("quantity", 1))

        product = get_object_or_404(Product, id=product_id)

        # Convert dates
        rental_start_date = datetime.strptime(rental_start_date, "%Y-%m-%d").date()
        rental_end_date = datetime.strptime(rental_end_date, "%Y-%m-%d").date()
        rental_days = (rental_end_date - rental_start_date).days

        if rental_days <= 0:
            return JsonResponse({"error": "Invalid rental period"}, status=400)

        # Check if the size exists and if stock is available
        try:
            product_size = ProductSize.objects.get(product=product, size=size)
        except ProductSize.DoesNotExist:
            return JsonResponse({"error": "Size not available for the selected product"}, status=400)

        # Check if the quantity is available
        if product_size.stock < quantity:
            return JsonResponse({"error": "Not enough stock available"}, status=400)

        # Add to cart
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product_size=product_size,
            rental_start_date=rental_start_date,
            rental_end_date=rental_end_date,
            defaults={"quantity": quantity},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return JsonResponse({"message": "Product added to cart", "cart_id": cart_item.id}, status=200)
    

# ==============================
#    CART
# ==============================



from django.db import transaction


def add_to_cart(request, product_id, size_id):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("product_detail", product_id=product_id)

    email = request.session.get("email")
    if not email:
        messages.error(request, "Please log in to continue.")
        return redirect("login")

    user = get_object_or_404(Login, email=email)
    product_size = get_object_or_404(ProductSize.objects.select_related("product"), id=size_id)

    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity <= 0:
            raise ValueError
    except ValueError:
        messages.error(request, "Invalid quantity.")
        return redirect("product_detail", product_id=product_id)

    if product_size.stock < quantity:
        messages.error(request, f"Only {product_size.stock} left in stock.")
        return redirect("product_detail", product_id=product_id)

    with transaction.atomic():
        cart_item, created = Cart.objects.get_or_create(user=user, product_size=product_size)
        cart_item.quantity = min(cart_item.quantity + quantity, product_size.stock) if not created else quantity
        cart_item.save()

    messages.success(request, f"{product_size.product.name} added to your cart!")
    return redirect("cart")

#     VIEW CART

def cart(request):
    email = request.session.get("email")
    if not email:
        messages.error(request, "You need to be logged in to view the cart.")
        return redirect("login")

    user = get_object_or_404(Login, email=email)

    # Fetch all cart items for this user
    cart_items = Cart.objects.filter(user=user)

    # Calculate Grand Total
    grand_total = sum(item.product_size.product.price * item.quantity for item in cart_items)

    return render(request, "cart.html", {"cart_items": cart_items, "grand_total": grand_total})



#     REMOVE FROM CART

def remove_from_cart(request, cart_id):
    email = request.session.get("email")
    user = get_object_or_404(Login, email=email)

    # Get the cart item using the cart ID
    cart_item = get_object_or_404(Cart, id=cart_id, user=user)
    cart_item.delete()

    messages.success(request, "Item removed from cart.")
    return redirect("cart")




#     UPDATE CART (WITH AJAX)

def update_cart(request, product_id):
    if request.method == "POST":
        try:
            new_quantity = int(request.POST.get('quantity', 1))

            email = request.session.get("email")
            user = get_object_or_404(Login, email=email)

            cart_item = get_object_or_404(Cart, user=user, product_id=product_id)

            if new_quantity > 0:
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                cart_item.delete()  # Remove item if quantity is zero

            messages.success(request, "Cart updated successfully!")

            # ✅ Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'new_quantity': cart_item.quantity})

        except ValueError:
            messages.error(request, "Invalid quantity.")

    return redirect('cart')



#     CLEAR CART

def clear_cart(request):
    email = request.session.get("email")
    user = get_object_or_404(Login, email=email)

    Cart.objects.filter(user=user).delete()
    messages.success(request, "Your cart has been cleared.")

    return redirect('cart')



#     MOVE TO WISHLIST
def move_to_wishlist(request, product_id):
    email = request.session.get("email")
    user = get_object_or_404(Login, email=email)

    cart_item = get_object_or_404(Cart, user=user, product_id=product_id)

    # ✅ Move product from cart to wishlist
    wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=cart_item.product)
    if created:
        messages.success(request, f"{cart_item.product.name} moved to wishlist!")
    else:
        messages.info(request, "Item is already in your wishlist.")

    cart_item.delete()  # ✅ Remove from cart after moving to wishlist

    return redirect('cart')



# ==============================
#    WISHLIST
# ==============================
# ⭐ View Wishlist
def wishlist_view(request):
    if "email" not in request.session:
        messages.error(request, "Please log in to access your wishlist.")
        return redirect("login")

    user = get_object_or_404(Login, email=request.session["email"])
    wishlist_items = Wishlist.objects.filter(user=user).select_related("product")

    return render(request, "wishlist.html", {"wishlist_items": wishlist_items})

# ⭐ Add to Wishlist
def add_to_wishlist(request, product_id):
    if "email" not in request.session:
        messages.error(request, "Please log in to add items to your wishlist.")
        return redirect("login")

    user = get_object_or_404(Login, email=request.session["email"])
    product = get_object_or_404(Product, id=product_id)

    wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)
    
    if created:
        messages.success(request, "Item added to wishlist successfully!")
    else:
        messages.info(request, "This item is already in your wishlist.")

    return redirect("wishlist")

# ⭐ Remove from Wishlist
def remove_from_wishlist(request, product_id):
    if "email" not in request.session:
        messages.error(request, "Please log in to remove items from your wishlist.")
        return redirect("login")

    user = get_object_or_404(Login, email=request.session["email"])

    if Wishlist.objects.filter(user=user, product_id=product_id).exists():
        Wishlist.objects.filter(user=user, product_id=product_id).delete()
        messages.success(request, "Item removed from wishlist successfully!")
    else:
        messages.error(request, "Item not found in wishlist.")

    return redirect("wishlist")


def add_to_cart_from_wishlist(request, product_id):
    if "email" not in request.session:
        messages.error(request, "Please log in to add items to your cart.")
        return redirect("login")

    user = get_object_or_404(Login, email=request.session["email"])
    product = get_object_or_404(Product, id=product_id)

    # Move product from wishlist to cart
    Wishlist.objects.filter(user=user, product=product).delete()
    Cart.objects.create(user=user, product=product, quantity=1)  # Adjust as needed

    messages.success(request, "Item moved to cart successfully!")
    return redirect("wishlist")

# ==============================
#    INVOICE
# ==============================
from django.urls import reverse

def invoice(request, booking_id):
    user_id = request.session.get("id")
    booking = get_object_or_404(Booking, id=booking_id, customer_id=user_id)

    # ✅ Notify the user about rental confirmation
    messages.success(request, "✅ Your rental has been confirmed! Redirecting to rental history...")

    # 🔹 Render invoice and set auto-redirect to rental history
    response = render(request, "invoice.html", {
        "booking": booking,
        "name": booking.booking_name,
        "address": booking.booking_address,
        "phone_number": booking.booking_phone,
    })


    response["Refresh"] = f"5; url={request.build_absolute_uri(reverse('rental_history'))}"

    return response

# ==============================
#    CHECKOUT
# ==============================


from decimal import Decimal, ROUND_HALF_UP 

def checkout(request):
    email = request.session.get("email")
    user = get_object_or_404(Login, email=email)

    cart_items = Cart.objects.filter(user=user)

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty!")
        return redirect('cart')

    # ✅ Always calculate totals, for GET and POST
    total_price = sum(item.quantity * item.product_size.product.price for item in cart_items)
    total_price = Decimal(total_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    security_deposit = (total_price * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    grand_total = (total_price + security_deposit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        landmark = request.POST.get('landmark', '')

        last_booking = None

        for item in cart_items:
            product_size = item.product_size
            employee = product_size.product.added_by

            last_booking = Booking.objects.create(
                customer=user,
                product_size=product_size,
                assigned_employee=employee,
                status=1,
                tracking_status="placed",
                is_active=True,
                booked_at=now(),
                return_by=now() + timedelta(days=7),
                security_deposit=(product_size.product.price * item.quantity * Decimal("0.10")).quantize(Decimal("0.01")),
                total_price=(product_size.product.price * item.quantity).quantize(Decimal("0.01")),
                booking_name=name,
                booking_address=f"{address}, Landmark: {landmark}",
                booking_phone=phone
            )

        cart_items.delete()
        messages.success(request, "Booking successful!")

        return redirect('payment_page', booking_id=last_booking.id)

    # ✅ Pass totals to template for GET request
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'security_deposit': security_deposit,
        'grand_total': grand_total
    })



# ==============================
#    ORDER HISTORY
# ==============================


def order_history(request):
    email = request.session.get("email")
    user = get_object_or_404(Login, email=email)

    # ✅ Fetch only "Paid" bookings for this user
    bookings = Booking.objects.filter(user=user, status="Paid").order_by("-rental_start_date")

    return render(request, "order_history.html", {"bookings": bookings})





# ==============================
#    RENTAL & PAYMENT PROCESSING
# ==============================


def rent_product(request, product_id):
    email = request.session.get("email")
    user = get_object_or_404(Login, email=email)

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
            rental_duration = int(request.POST.get("rental_duration", 1))

            if quantity < 1 or rental_duration < 1:
                messages.error(request, "Invalid quantity or rental duration.")
                return redirect("rent_product", product_id=product.id)

            total_price = product.price * quantity * rental_duration

            # ✅ Create a Booking entry
            booking = Booking.objects.create(
                user=user,
                product=product,
                quantity=quantity,
                rental_start_date=now(),
                rental_end_date=now() + timedelta(days=rental_duration),
                total_price=total_price,
                status="1"
            )

            messages.success(request, "Rental request submitted! Proceed to payment.")
            return redirect("booking_confirmation", booking_id=booking.id)

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("rent_product", product_id=product.id)

    return render(request, "rent_product.html", {"product": product})



def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "booking_confirmation.html", {"booking": booking})


# ==============================
#    PAYMENT PROCESSING (RAZORPAY)
# ==============================

def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
    order_amount = int(booking.total_price * 100)  # Convert to paisa
    order_currency = "INR"

    try:
        razorpay_order = client.order.create({
            "amount": order_amount,
            "currency": order_currency,
            "payment_capture": "1"
        })
    except:
        return render(request, "payment_page.html", {"error": "Payment gateway issue. Please try again."})

    return render(request, "payment_page.html", {
        "booking": booking,
        "order": razorpay_order,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "security_deposit": booking.security_deposit,
    })


def confirm_order(request, booking_id):
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=booking_id)

        # ✅ Extract RazorpayX response data
        payment_id = request.POST.get("razorpay_payment_id")
        order_id = request.POST.get("razorpay_order_id")
        signature = request.POST.get("razorpay_signature")

        # ✅ Ensure a Payment entry exists
        payment, created = Payment.objects.get_or_create(
            booking=booking,
            defaults={
                "amount": booking.total_price,
                "payment_method": 1,  # Assuming UPI (change if needed)
                "status": 0,  # Pending
            },
        )

        # ✅ Initialize RazorpayX Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

        try:
            # ✅ Verify the payment signature
            client.utility.verify_payment_signature({
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_id,
                "razorpay_signature": signature
            })

            # ✅ Fetch payment details from RazorpayX
            payment_details = client.payment.fetch(payment_id)

            if payment_details["status"] == "captured":
                # ✅ Update payment record as successful
                payment.transaction_id = payment_id
                payment.status = 1  # Successful
                payment.save()

                return JsonResponse({"success": True, "redirect_url": f"/invoice/{booking.id}/"})

            else:
                payment.status = 2  # Failed
                payment.save()
                return JsonResponse({"success": False, "message": "Payment failed. Please try again."})

        except razorpay.errors.SignatureVerificationError:
            payment.status = 2  # Failed
            payment.save()
            return JsonResponse({"success": False, "message": "Payment verification failed. Please try again."})

    return JsonResponse({"success": False, "message": "Invalid request."})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Booking, Return, Payment, Rental, ProductSize

# ==============================
#     EMPLOYEE - INSPECT RETURNED ITEM
# ==============================

from django.contrib import messages
from django.http import HttpResponseNotFound

def confirm_refund(request, id):
    # Fetch the booking using the 'id'
    booking = get_object_or_404(Booking, id=id)

    # Check if the tracking status is 'Returned'
    if booking.tracking_status != 'returned':
        return HttpResponseNotFound(f"Booking {id} has not been returned yet.")

    if request.method == "POST":
        refund_status = request.POST.get("refund_status")
        late_fee = request.POST.get("late_fee")
        note = request.POST.get("note")

        # Handle the refund logic
        if refund_status == "confirmed":
            booking.status = 1
            booking.tracking_status = "Refunded"  # Mark the tracking status as refunded
        elif refund_status == "rejected":
            booking.status = 2
        else:
            return HttpResponseNotFound(f"Invalid refund status for booking {id}.")  # Handle invalid status

        # Handle late fee (if any)
        if late_fee:
            try:
                late_fee = float(late_fee)  # Ensure the late fee is a valid number
                booking.late_fee = late_fee
            except ValueError:
                return HttpResponseNotFound("Invalid late fee value.")  # Handle invalid late fee input

        # Save inspection notes (if necessary)
        if note:
            booking.inspection_note = note  # Add inspection note to the booking

        # Save all changes to the booking in one go
        booking.save()

        # Redirect or show success message
        return redirect('employee_bookings')  # Adjust as necessary

    return render(request, 'employee_confirm_refund.html', {
        'id': id,
        'booking':booking
        
    })

# ==============================
#     ADMIN - PROCESS REFUND
# ==============================

def process_refund(request, payment_id):
    """Admin processes the refund based on the employee's confirmation and any deductions."""
    
    # Fetch the payment and related booking
    payment = get_object_or_404(Payment, id=payment_id)
    booking = payment.booking
    
    # Try to fetch the related Return object, if it exists
    try:
        returned_item = Return.objects.get(booking=booking)
    except Return.DoesNotExist:
        messages.error(request, "No return record found for this booking.")
     #   return redirect("admin_payment")  # Redirect to the admin payments page

    # Check if the item has been confirmed for refund by the employee
    # if returned_item.refund_status != "confirmed":
    #     messages.error(request, "Refund cannot be processed. Employee has not confirmed it.")
      #  return redirect("admin_payment")

    # Retrieve the security deposit, late fee, and damage fee
    security_deposit = booking.security_deposit or 0
    late_fee = returned_item.late_fee or 0
    damage_fee = getattr(returned_item, 'damage_fee', 0) or 0
    
    # Calculate total deductions
    total_deductions = late_fee + damage_fee
    
    # Calculate refund amount, ensuring it doesn't go below 0
    refund_amount = max(0, security_deposit - total_deductions)

    # Process the refund if the refund button is clicked
        # Update payment with the refund status and amount
    payment.refund_status = "approved" if refund_amount > 0 else "rejected"
    payment.refund_amount = refund_amount
    payment.security_deposit_refunded = True
    payment.save()

        # Display success or failure message
    if refund_amount > 0:
        messages.success(request, f"Refund of ₹{refund_amount} processed successfully.")
    else:
        messages.success(request, "Refund rejected due to deductions exceeding the security deposit.")

    #return redirect("admin_payment")

    # Render the refund processing page with the necessary context
    return render(request, "admin_process_refund.html", {
        "payment": payment,
        "booking": booking,
        "returned_item": returned_item,
        "refund_amount": refund_amount,
    })

# ==============================
#     EMPLOYEE - UPDATE BOOKING STATUS
# ==============================

def update_booking_status(request, booking_id):
    """Employees update booking status and track product state."""
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        valid_statuses = ["pending", "shipped", "out for delivery", "returned", "inspected"]

        if new_status not in valid_statuses:
            messages.error(request, "Invalid status update.")
            return redirect("employee_dashboard")

        booking.status = new_status
        booking.save()

        # Product tracking logic
        if new_status == "returned":
            # Mark rental inactive
            Rental.objects.filter(booking=booking).update(is_active=False)

            # Restock the product
            product_size = booking.product_size
            product_size.stock += 1
            product_size.save()

        elif new_status == "inspected":
            # Mark the rental as completed if inspected after return
            Rental.objects.filter(booking=booking).update(is_active=False)

        messages.success(request, f"Booking status updated to {new_status}.")
        return redirect("employee_dashboard")

    return render(request, "update_booking_status.html", {"booking": booking})


def my_bookings(request):
    email = request.session.get('email')  # Email stored in session
    if not email:
        return redirect('login')  # or your login URL name

    try:
        employee = Employee.objects.get(user__email=email)
    except Employee.DoesNotExist:
        return render(request, 'error.html', {'message': 'Employee not found'})

    # Get all products added by this employee
    product_ids = Product.objects.filter(added_by=employee).values_list('id', flat=True)

    # Get product sizes of those products
    size_ids = ProductSize.objects.filter(product_id__in=product_ids).values_list('id', flat=True)

    # Get bookings made for those product sizes
    bookings = Booking.objects.filter(product_size_id__in=size_ids)

    # Get return info related to those bookings
    returns = Return.objects.filter(booking__in=bookings)

    context = {
        'bookings': bookings,
        'returns': returns,
    }
    return render(request, 'my_bookings.html', context)

# ==============================
#    PRODUCT REVIEW
# ==============================
def review_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            # Save the review for the product
            review = form.save(commit=False)
            review.product = product
            review.user = request.user  # Assuming the user is logged in
            review.save()
            return redirect('product_details', product_id=product.id)
    else:
        form = ProductReviewForm()

    return render(request, 'review.html', {'form': form, 'product': product})
  
# ==============================
#    ADMIN PAYMENT STATUS VIEW
# ==============================
def admin_payment(request):
    payments = Payment.objects.all().order_by('-payment_date')  # ✅ Correct field name
    return render(request, "admin_payment.html", {"payments": payments})


# ==============================
#    ADMIN COMPLAINT VIEW
# ==============================
from django.utils import timezone
# Admin View: All Complaints

def admin_resolve_complaints(request):
    """
    Displays all complaints for the admin to review.
    """
    start_date = timezone.now() - timedelta(days=30)
    complaints = Complaint.objects.filter(submitted_at__gte=start_date).order_by('-submitted_at')
    return render(request, 'admin_resolve_complaints.html', {'complaints': complaints})


# -------------------------------
# Admin View: Reply to Complaint
# -------------------------------
def reply_user_complaint(request, complaint_id):
    """
    Admin replies to a complaint and marks it as Resolved.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        response_text = request.POST.get("response")
        if response_text:
            complaint.status = 1  # Resolved
            complaint.resolved_at = timezone.now()
            complaint.save()
            # You may store the response in another model or send notification if needed
            messages.success(request, f"Replied to complaint #{complaint.id} successfully!")
        else:
            messages.error(request, "Response cannot be empty.")

    return redirect("admin_resolve_complaints")


# -------------------------------
# Admin View: Mark as Resolved Without Reply
# -------------------------------
def resolve_complaints(request, complaint_id):
    """
    Marks complaint as resolved without an explicit reply.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)
    complaint.status = 1  # Resolved
    complaint.resolved_at = timezone.now()
    complaint.save()
    messages.success(request, f"Complaint #{complaint_id} has been marked as resolved.")
    return redirect('admin_resolve_complaints')


# ==============================
#    EMPLOYEE BOOKING VIEW
# ==============================

def employee_bookings(request):
    """Display bookings only for products added by the logged-in employee."""
    user_id = request.session.get("id")  # Corrected from 'user_type' to 'id'
    try:
        employee = Employee.objects.get(user=user_id)
    except Employee.DoesNotExist:
        messages.error(request, "No employee profile found.")
        return redirect("login")  

    # Fetch bookings where the product's added_by is the current employee
    bookings = Booking.objects.filter(
        product_size__product__added_by=employee,
        is_active=True
    ).select_related('product_size__product').order_by("-booked_at")

    return render(request, "employee_bookings.html", {"bookings": bookings})


def employee_update_booking(request, booking_id):
    """Allow updating tracking only for employee's own added product bookings."""
    user_id = request.session.get("id")
    employee = get_object_or_404(Employee, user=user_id)

    # Booking must be for a product added by this employee
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        product_size__product__added_by=employee  # Ensures ownership
    )

    if request.method == 'POST':
        new_status = request.POST.get('tracking_status')  # string value
        if new_status in dict(Booking.TRACKING_CHOICES).keys():
            booking.tracking_status = new_status
            booking.save()
            messages.success(request, "Booking status updated successfully.")
            return redirect('employee_bookings')
        else:
            messages.error(request, "Invalid tracking status selected.")

    return render(request, 'employee_update_booking.html', {'booking': booking})

# ==============================
#    CUSTOMER COMPLAINTS
# ==============================
def complaint(request):
    if request.session.get("user_type") != "1":
        messages.error(request, "Please login as a customer to submit a complaint.")
        return redirect("login")

    email = request.session.get("email")
    login_instance = get_object_or_404(Login, email=email)

    if request.method == "POST":
        message = request.POST.get("complaint", "").strip()  # fixed field name

        if not message:
            messages.error(request, "Please enter a complaint message.")
            return redirect("complaint")

        Complaint.objects.create(user=login_instance, message=message)
        messages.success(request, "Complaint submitted successfully.")
        return redirect("customer_dashboard")

    return render(request, "complaint.html")



def complaints(request):
    if request.session.get("user_type") != "1":
        messages.error(request, "Please login as a customer to view complaints.")
        return redirect("login")
    
    email = request.session.get("email")
    login_instance = get_object_or_404(Login, email=email)
    
    complaints = Complaint.objects.filter(user=login_instance).order_by('-submitted_at')
    
    return render(request, 'complaint.html', {'complaint': complaint})


# ==============================
#    EMPLOYEE COMPLAINT VIEW
# ==============================

def employee_complaints(request):
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied: Only employees can manage customer complaints.")
        return redirect("login")
    
    # Get employee details
    email = request.session.get("email")
    try:
        login_instance = Login.objects.get(email=email)
        employee = Employee.objects.get(user=login_instance)
        
        # Only managers (position 1) should be able to manage complaints
        if employee.position != "1":  # Manager
            messages.error(request, "Only managers can handle customer complaints.")
            return redirect("employee_dashboard")
            
    except (Login.DoesNotExist, Employee.DoesNotExist):
        messages.error(request, "Employee profile not found.")
        return redirect("login")
    
    # Get filter parameter
    filter_by = request.GET.get('filter', 'pending')
    
    if filter_by == 'pending':
        complaints = Complaint.objects.filter(status=0)  # Pending
    elif filter_by == 'resolved':
        complaints = Complaint.objects.filter(status=1)  # Resolved
    elif filter_by == 'dismissed':
        complaints = Complaint.objects.filter(status=2)  # Dismissed
    else:
        complaints = Complaint.objects.all()
    
    # Order by submission date
    complaints = complaints.order_by('-submitted_at')
    
    return render(request, 'employee_complaints.html', {
        'complaints': complaints,
        'filter': filter_by,
        'employee': employee
    })

def employee_resolve_complaint(request, complaint_id):
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied: Only employees can resolve complaints.")
        return redirect("login")
    
    # Get employee details
    email = request.session.get("email")
    try:
        login_instance = Login.objects.get(email=email)
        employee = Employee.objects.get(user=login_instance)

        if employee.position != "1":  # Only Manager
            messages.error(request, "Only managers can resolve customer complaints.")
            return redirect("employee_dashboard")
            
    except (Login.DoesNotExist, Employee.DoesNotExist):
        messages.error(request, "Employee profile not found.")
        return redirect("login")
    
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        # No resolution message since field is removed
        complaint.status = 1  # Mark as Resolved
        complaint.resolved_at = now()
        complaint.save()

        messages.success(request, "Complaint has been resolved successfully.")

    return redirect('employee_complaints')

def employee_view_complaint(request, complaint_id):
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied: Only employees can view complaint details.")
        return redirect("login")
    
    # Get employee details
    email = request.session.get("email")
    try:
        login_instance = Login.objects.get(email=email)
        employee = Employee.objects.get(user=login_instance)
        
        # Only managers (position 1) should be able to view complaints
        if employee.position != "1":  # Manager
            messages.error(request, "Only managers can view customer complaints.")
            return redirect("employee_dashboard")
            
    except (Login.DoesNotExist, Employee.DoesNotExist):
        messages.error(request, "Employee profile not found.")
        return redirect("login")
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Get related booking information if available
    booking_info = None
    if complaint.booking:
        booking_info = {
            'id': complaint.booking.id,
            'date': complaint.booking.booked_at,
            'status': complaint.booking.get_status_display(),
            'rentals': Rental.objects.filter(booking=complaint.booking)
        }
    
    context = {
        'complaint': complaint,
        'booking_info': booking_info,
        'employee': employee
    }
    
    return render(request, 'employee_complaint.html', context)

# ==============================
#    FEEDBACK
# ==============================

def submit_feedback(request, product_id):
    if request.method == "POST":
        email = request.session.get("email")  # Get user email from session
        if not email:
            return redirect("login_page")

        user = Login.objects.filter(email=email).first()  # Get the user
        product = get_object_or_404(Product, id=product_id)

        rating = request.POST.get("rating")
        message = request.POST.get("review_text", "").strip()

        if rating and message and rating.isdigit():
            Feedback.objects.create(user=user, product=product, rating=int(rating), message=message)

        return redirect("product_details", product_id=product.id)

    return redirect("product_details", product_id=product_id)


# ==============================
#    ADMIN REPORT VIEW
# ==============================

# View all reports (submitted by employees)
def view_reports(request):
    reports = Report.objects.all().order_by('-created_at')  # Show latest first
    return render(request, 'view_reports.html', {'reports': reports})

# Approve a report
def approve_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    report.status = "Verified"
    report.verified_by = request.user.userprofile  # Assuming admin is logged in
    report.save()
    messages.success(request, "Report approved successfully.")
    return redirect('view_reports')

# Reject a report
def reject_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    report.status = "Rejected"
    report.save()
    messages.error(request, "Report has been rejected.")
    return redirect('view_reports')

# Generate Admin Reports
def generate_admin_report(request):
    filter_type = request.GET.get('filter', 'all')

    if filter_type == 'sales':
        reports = Report.objects.filter(title__icontains="sales")
    elif filter_type == 'inventory':
        reports = Report.objects.filter(title__icontains="inventory")
    elif filter_type == 'complaints':
        reports = Report.objects.filter(title__icontains="complaint")
    else:
        reports = Report.objects.all()  # Default: all reports

    return render(request, 'admin_dashboard/generate_admin_report.html', {'reports': reports, 'filter_type': filter_type})

# Export reports as PDF
def export_reports_pdf(request):
    reports = Report.objects.all()
    template_path = 'admin_dashboard/reports_pdf_template.html'
    context = {'reports': reports}
    
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reports.pdf"'

    pdf = pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=response)
    if pdf.err:
        return HttpResponse('Error generating PDF', status=400)

    return response




# ==============================
#    EMPLOYEE REPORT 
# ==============================


def employee_reports(request):
    """Employees can view their submitted reports and submit new ones."""
    u=request.session.get("id")
    # employee = get_object_or_404(Employee, user=u)
    reports = Report.objects.filter(id=u).order_by('-created_at')

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if title and description:
            Report.objects.create(employee=u, title=title, description=description)
            messages.success(request, "Report submitted successfully! Awaiting admin verification.")
            return redirect("employee_reports")
        else:
            messages.error(request, "Title and description are required!")

    return render(request, "employee_reports.html", {"reports": reports})


# ==============================
#    CUSTOMER PROFILE MANAGEMENT 
# ==============================

def profile_management(request):
    u = request.session.get("id")

    try:
        user_profile = UserProfile.objects.get(id=u)
    except UserProfile.DoesNotExist:
        user_profile = None

    if request.method == 'POST':
        # Update Profile Picture Only
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES.get('profile_picture')
            if user_profile:
                user_profile.profile_picture = profile_picture
                user_profile.save()
            else:
                UserProfile.objects.create(
                    user=request.user,
                    profile_picture=profile_picture,
                )

        # Update Profile Details (Full Name, Phone, Email)
        elif all(field in request.POST for field in ['full_name', 'phone', 'email']):
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')

            if user_profile:
                user_profile.full_name = full_name
                user_profile.phone = phone
                user_profile.save()
            else:
                user_profile = UserProfile.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone=phone
                )
            request.user.email = email
            request.user.save()

        # Password Update
        elif 'new_password' in request.POST:
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            current_password = request.POST.get('current_password')

            if new_password == confirm_password:
                request.user.password = new_password  # Still plain text (not secure!)
                request.user.save()
            else:
                messages.error(request, "Passwords do not match.")

        return redirect('profile_management')

    return render(request, 'profile_management.html', {
        'user_profile': user_profile,
        'user': request.user
    })

# ==============================
#     RENTAL HISTORY
# ==============================

def rental_history(request):
    # Get all bookings for the logged-in user (past and current)
    u=request.session.get("id")

    bookings = Booking.objects.filter(customer=u).order_by('-booked_at')
    
    # Optionally, filter out only completed rentals or other criteria
    completed_rentals = Rental.objects.filter(customer=u, is_active=False)
    
    return render(request, 'rental_history.html', {
        'bookings': bookings,
        'completed_rentals': completed_rentals,
    })


def cancel_booking(request, booking_id):
    if request.method == "POST":
        user_id = request.session.get("id")
        booking = get_object_or_404(Booking, id=booking_id, customer_id=user_id)

        # Only cancel if it's still pending and not returned
        if booking.status == 1 and booking.tracking_status.lower() != "returned":
            booking.status = 4  # Cancelled
            booking.is_active = False
            booking.save()
            messages.success(request, "Booking has been cancelled successfully.")
        else:
            messages.warning(request, "This booking cannot be cancelled.")
    
    return redirect("rental_history")

def update_tracking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        new_status = request.POST.get("tracking_status")
        booking.tracking_status = new_status

        # Get the currently logged-in employee
        employee = Employee.objects.filter(user=request.user).first()
        if employee:
            booking.tracking_updated_by = employee
        
        booking.save()
        messages.success(request, "Tracking status updated.")
        return redirect('employee_booking')  # adjust route as needed

    return render(request, 'update_tracking.html', {'booking': booking})



# ==============================
#     CHATBOT ASSISTANCE
# ==============================
from django.views.decorators.http import require_http_methods
# Default predefined answers
DEFAULT_RESPONSES = {
    "rental policy": "You can rent items for up to 7 days. Late returns may incur additional charges.",
    "available sizes": "Our sizes range from XS to XXL. Check the size chart for details.",
    "hi": "Hello! 😊 How can I assist you with your wardrobe rental today?",
    "how to rent": "To rent an item, browse the catalog, select a size, and proceed to checkout.",
    "track order": "You can track your order under 'My Bookings'.",
    "refund process": "Refunds are processed after inspection and admin confirmation.",
    "recommend accessories": "Recommended accessories are shown on the product detail page.",
    "feedback": "You can submit feedback under 'My Bookings' after your rental is complete.",
    "help": "You can ask about rentals, returns, payments, booking status, or product availability.",
}


@require_http_methods(["GET", "POST"])
def chatbot_view(request):
    if request.method == "POST":
        user_query = request.POST.get("user_query", "").strip().lower()

        if not user_query:
            return JsonResponse({"response": "Please enter a valid question.", "recommendations": []})

        # Save or fetch query from DB
        chat_entry, created = ChatbotQuery.objects.get_or_create(user=request.user if request.user.is_authenticated else None, query=user_query)

        if not created and chat_entry.response:
            response = chat_entry.response
        else:
            response = DEFAULT_RESPONSES.get(user_query, "I'm sorry, I don't have an answer for that yet.")
            chat_entry.response = response
            chat_entry.save()

        # Fetch related product recommendations
        recommendations = []
        matched_products = Product.objects.filter(name__icontains=user_query)

        for product in matched_products:
            recs = ProductRecommendation.objects.filter(product=product)
            recommendations.extend([r.recommended_product.name for r in recs])

        return JsonResponse({"response": response, "recommendations": recommendations})

    return render(request, "chatbot.html")


@require_http_methods(["POST"])
def chatbot_response_json(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip().lower()

        if not user_message:
            return JsonResponse({"response": "Please type something to get started."})

        response = DEFAULT_RESPONSES.get(user_message, "I'm here to help! Try asking about 'how to rent' or 'track order'.")

        return JsonResponse({"response": response})

    except Exception as e:
        return JsonResponse({"response": "Oops, something went wrong. Please try again."})


def get_previous_queries(request):
    if request.user.is_authenticated:
        queries = ChatbotQuery.objects.filter(user=request.user).order_by('-timestamp').values_list('query', flat=True).distinct()[:10]
    else:
        queries = ChatbotQuery.objects.filter(user=None).order_by('-timestamp').values_list('query', flat=True).distinct()[:10]

    return JsonResponse({"queries": list(queries)})

def add_recommendations(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    all_products = Product.objects.exclude(id=product_id)  # exclude main product
    recommendation_types = ProductRecommendation.RECOMMENDATION_TYPE_CHOICES
    selected_type = request.GET.get('recommendation_type', 'accessory')  # default type

    # Get already recommended products for the selected type
    existing_recommendations = ProductRecommendation.objects.filter(
        product=product,
        recommendation_type=selected_type
    ).values_list('recommended_product__id', flat=True)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('recommended_products')
        selected_type = request.POST.get('recommendation_type', 'accessory')

        # Delete old recommendations of this type
        ProductRecommendation.objects.filter(product=product, recommendation_type=selected_type).delete()

        for pid in selected_ids:
            recommended = get_object_or_404(Product, id=pid)
            ProductRecommendation.objects.create(
                product=product,
                recommended_product=recommended,
                recommendation_type=selected_type
            )

        messages.success(request, "Recommendations updated successfully.")
        return redirect('admin_manage_inventory')

    return render(request, 'admin_add_recommendation.html', {
        'product': product,
        'all_products': all_products,
        'recommendation_types': recommendation_types,
        'selected_type': selected_type,
        'existing_ids': list(existing_recommendations),  # send to template
    })

def get_recommendations(request, product_id):
    """
    Retrieves recommended products for a given product.
    """
    product = get_object_or_404(Product, id=product_id)
    recommendations = ProductRecommendation.objects.filter(product=product).select_related("recommended_product")

    formatted_data = {}
    for rec in recommendations:
        rec_type = rec.recommendation_type
        if rec_type not in formatted_data:
            formatted_data[rec_type] = []
        formatted_data[rec_type].append({
            "id": rec.recommended_product.id,
            "name": rec.recommended_product.name
        })

    return JsonResponse(formatted_data, safe=False)
# ==============================
#     OTHERS
# ==============================
def sustainability_impact(request):
    return render(request, "sustainability_impact.html")

def support_center(request):
    return render(request, "support_center.html")
