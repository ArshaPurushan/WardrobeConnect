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
from .models import Product, ProductSize, Rental, Payment, Booking
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

def manage_users(request):
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
#    PRODUCT MANAGEMENT (employee)
# ==============================
from django.db.models import Sum
def employee_inventory(request):
    """ Display inventory for employees. """
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied: Only employees can access inventory.")
        return redirect("login")

    products = Product.objects.all()  # Fetch all products
    
    # Get employee details for tracking who added products
    email = request.session.get("email")
    try:
        login_instance = Login.objects.get(email=email)
        employee = Employee.objects.get(user=login_instance)
        
        # Filter products added by this employee if requested
        filter_by = request.GET.get('filter')
        if filter_by == 'my_products':
            products = products.filter(added_by=employee)
    except (Login.DoesNotExist, Employee.DoesNotExist):
        employee = None

    # Annotate products with total stock and available sizes
    for product in products:
        product.total_stock = ProductSize.objects.filter(product=product).aggregate(Sum("stock"))["stock__sum"] or 0
        product.available_sizes = list(ProductSize.objects.filter(product=product).values_list("size", flat=True))

    return render(request, "employee_inventory.html", {"products": products, "employee": employee})

def add_product(request):
    """Handle adding product and its sizes with stock to the database."""
    
    if request.method == "POST":
        # Step 1: Get the product data from the form
        product_name = request.POST.get('name')
        product_category = request.POST.get('category')
        product_subcategory = request.POST.get('subcategory')
        product_price = request.POST.get('price')
        product_description = request.POST.get('description')
        product_image = request.FILES.get('image')  # Image file
        product_availability = request.POST.get('availability')
        product_gender = request.POST.get('gender')

        # Step 2: Create a new Product instance and save it
        product = Product.objects.create(
            name=product_name,
            category=product_category,
            subcategory=product_subcategory,
            price=product_price,
            description=product_description,
            image=product_image,
            availability=product_availability,
            gender=product_gender
        )

        # Step 3: Get the size and stock data from the POST request
        sizes = request.POST.getlist('sizes')  # List of selected sizes
        for size in sizes:
            stock = int(request.POST.get(f"stock_{size}", 0))  # Get stock for each size

            # Step 4: Create ProductSize for each size
            ProductSize.objects.create(
                product=product,
                size=size,
                stock=stock
            )

        # Step 5: Success message and redirect
        messages.success(request, "Product added successfully!")
        return redirect('employee_inventory')  # Redirect to the product list page after successful addition.

    return render(request, 'employee_add_product.html')  # Render the form template


def edit_product(request, product_id):
    """Fetch and update product details, including sizes and stock."""
    product = get_object_or_404(Product, id=product_id)
    product_sizes = ProductSize.objects.filter(product=product)

    # Extract sizes as a list to use in the template
    selected_sizes = [size.size for size in product_sizes]

    if request.method == "POST":
        product.name = request.POST.get('name')
        product.category = request.POST.get('category')
        product.subcategory = request.POST.get('subcategory')
        product.price = request.POST.get('price')
        product.description = request.POST.get('description')
        product.availability = request.POST.get('availability')
        product.gender = request.POST.get('gender')

        if 'image' in request.FILES:
            product.image = request.FILES['image']  # Update image only if a new one is uploaded

        product.save()

        # Update Stock for Each Size
        sizes = request.POST.getlist('sizes')
        existing_sizes = {ps.size: ps for ps in product_sizes}  # Dictionary of existing sizes

        for size in sizes:
            stock = int(request.POST.get(f'stock_{size}', 0))

            if size in existing_sizes:
                existing_sizes[size].stock = stock
                existing_sizes[size].save()
            else:
                ProductSize.objects.create(product=product, size=size, stock=stock)

        messages.success(request, "Product updated successfully!")
        return redirect('employee_inventory')
        #return redirect('edit_product', product_id=product.id)

    return render(request, 'employee_edit_product.html', {
        'product': product,
        'product_sizes': product_sizes,
        'selected_sizes': selected_sizes,  # Pass the selected sizes
    })





def delete_product(request, product_id):
    """ Allow inventory managers to delete products. """
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied: Only employees can delete products.")
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    # Check if product is in active rental
    if Rental.objects.filter(product_size__product=product, is_active=True).exists():
        messages.error(request, "Cannot delete product that is currently rented.")
        return redirect("employee_inventory")

    if request.method == "POST":
        product.delete()
        messages.success(request, f"Product '{product.name}' deleted successfully!")
    
    return redirect("employee_inventory")

def update_availability(request, product_id):
    """ Employees can update product availability (e.g., mark as rented, returned). """
    if request.session.get("user_type") != "2":
        messages.error(request, "Access Denied: Only employees can update availability.")
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        availability = int(request.POST.get("availability"))

        if availability in dict(Product.AVAILABILITY_CHOICES):
            product.availability = availability
            product.save()
            
            # If product is marked damaged, check if it should be removed
            if availability == 3:  # Damaged
                product.remove_if_damaged()
                messages.warning(request, f"Product '{product.name}' marked as damaged.")
            else:
                messages.success(request, f"Product availability updated to '{product.get_availability_display()}'.")
        else:
            messages.error(request, "Invalid availability status selected.")

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
    products = Product.objects.filter(availability=0)

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
#    PRODUCT DETAILS 
# ==============================

def product_details(request, product_id):
    # Get the main product
    product = get_object_or_404(Product, id=product_id)

    # Get available sizes for the product
    available_sizes = ProductSize.objects.filter(product=product, stock__gt=0)  # Only show in-stock sizes
        # For debugging purposes, print the available sizes
    print(f"Available sizes for product {product_id}: {available_sizes}")

    # Get recommended products for the product
    recommended_products = ProductRecommendation.objects.filter(product=product)
    
    # List of recommended products
    recommended_product_list = [rec.recommended_product for rec in recommended_products]

    return render(request, "product_details.html", {
        "product": product,
        "available_sizes": available_sizes,  # Pass available sizes to the template
        "recommended_products": recommended_product_list,
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
    booking = get_object_or_404(Booking, id=booking_id, customer=request.session["id"])  # Ensure only the correct user can view it

    # 🔹 Render invoice and set auto-redirect to rental history
    response = render(request, "invoice.html", {"booking": booking})

    # ✅ Notify the user about rental confirmation
    messages.success(request, "✅ Your rental has been confirmed! Redirecting to rental history...")

    # ✅ Redirect to rental history after 5 seconds
    response["Refresh"] = f"5; url={request.build_absolute_uri(reverse('rental_history'))}"

    return response

# ==============================
#    CHECKOUT
# ==============================


from decimal import Decimal

def checkout(request):
    email = request.session.get("email")
    user = get_object_or_404(Login, email=email)

    cart_items = Cart.objects.filter(user=user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    total_price = sum(item.quantity * item.product_size.product.price for item in cart_items)
    total_price = Decimal(total_price)  # Convert sum to Decimal
    security_deposit = total_price * Decimal("0.10")   
    grand_total = total_price + security_deposit

    booking, _ = Booking.objects.get_or_create(customer=user, status=1)
    booking.total_price = grand_total
    booking.save()

    return render(request, "checkout.html", {
        "cart_items": cart_items,
        "subtotal": total_price,
        "security_deposit": security_deposit,
        "grand_total": grand_total,
        "booking": booking
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

# ==============================
#     REFUND
# ==============================

@login_required
def inspect_returned_item(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        damage_fee = float(request.POST.get("damage_fee", 0))
        late_fee = float(request.POST.get("late_fee", 0))

        booking.damage_fee = damage_fee
        booking.late_fee = late_fee
        booking.save()

        messages.success(request, "Inspection completed! Admin will process the refund.")
        return redirect("employee_dashboard")

    return render(request, "inspect_return.html", {"booking": booking})

@login_required
def process_refund(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    refund_amount = booking.calculate_final_refund()

    if refund_amount > 0:
        payment = Payment.objects.get(booking=booking)
        payment.process_refund(refund_amount)
        booking.refund_status = "Refunded"
    else:
        booking.refund_status = "Deducted"

    booking.save()
    messages.success(request, f"Refund processed: ₹{refund_amount} returned to the customer.")
    return redirect("admin_dashboard")



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
    payments = Payment.objects.all().order_by('-date')  # Fetch payments sorted by date
    return render(request, "admin_payment.html", {"payments": payments})

# ==============================
#    ADMIN COMPLAINT VIEW
# ==============================
def admin_resolve_complaints(request):
    """
    Fetches and displays all complaints for the admin to review and manage.
    """
    complaints = Complaint.objects.all().order_by('-created_at')  # Sort by latest complaints
    return render(request, 'admin_resolve_complaints.html', {'complaints': complaints})

def reply_user_complaint(request, complaint_id):
    """Admin submits a reply to a complaint."""
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        response_text = request.POST.get("response")
        if response_text:
            complaint.admin_response = response_text
            complaint.status = "Resolved"
            complaint.save()
            messages.success(request, f"Replied to complaint #{complaint.id} successfully!")
        else:
            messages.error(request, "Response cannot be empty.")

    return redirect("admin_resolve_complaints")

def resolve_complaints(request, complaint_id):
    """
    Marks a complaint as resolved by the admin.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)
    complaint.status = "Resolved"
    complaint.save()
    messages.success(request, f"Complaint #{complaint_id} has been marked as resolved.")
    return redirect('admin_resolve_complaints')


# ==============================
#    EMPLOYEE BOOKING VIEW
# ==============================

def employee_bookings(request):
    """Display all bookings assigned to the logged-in employee."""
    # if request.session.get("user_type") != "2":
    #     messages.error(request, "Access Denied: Only employees can view bookings.")
    #     return redirect("login")

    # Get the logged-in employee
    u=request.session.get("user_type")
    try:
        employee = Employee.objects.get(user=u)
    except Employee.DoesNotExist:
        messages.error(request, "No employee profile found.")
        return redirect("login")  

    # Fetch bookings assigned to this employee
    bookings = Booking.objects.filter(assigned_employee=employee, is_active=True).order_by("-booked_at")

    return render(request, "employee_bookings.html", {"bookings": bookings})


# ==============================
#    CUSTOMER COMPLAINTS
# ==============================

def complaint(request):
    if request.session.get("user_type") != "1":
        messages.error(request, "Please login as a customer to submit complaints.")
        return redirect("login")
    
    email = request.session.get("email")
    login_instance = get_object_or_404(Login, email=email)
    
    # Get user's bookings for dropdown
    bookings = Booking.objects.filter(customer=login_instance)
    
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        message = request.POST.get("message", "").strip()
        
        if not message:
            messages.error(request, "Please provide a complaint message.")
            return render(request, 'submit_complaint.html', {'bookings': bookings})
        
        # Create complaint
        if booking_id and booking_id != "0":
            booking = get_object_or_404(Booking, id=booking_id, customer=login_instance)
            complaint = Complaint.objects.create(
                user=login_instance,
                booking=booking,
                message=message
            )
        else:
            # General complaint without booking reference
            complaint = Complaint.objects.create(
                user=login_instance,
                message=message
            )
        
        messages.success(request, "Your complaint has been submitted successfully.")
        return redirect("customerr_dashboard")
    
    return render(request, 'complaint.html', {'bookings': bookings})

def complaints(request):
    if request.session.get("user_type") != "1":
        messages.error(request, "Please login as a customer to view complaints.")
        return redirect("login")
    
    email = request.session.get("email")
    login_instance = get_object_or_404(Login, email=email)
    
    complaints = Complaint.objects.filter(user=login_instance).order_by('-submitted_at')
    
    return render(request, 'complaints.html', {'complaints': complaints})


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
        
        # Only managers (position 1) should be able to resolve complaints
        if employee.position != "1":  # Manager
            messages.error(request, "Only managers can resolve customer complaints.")
            return redirect("employee_dashboard")
            
    except (Login.DoesNotExist, Employee.DoesNotExist):
        messages.error(request, "Employee profile not found.")
        return redirect("login")
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == "POST":
        resolution = request.POST.get("resolution", "").strip()
        
        if not resolution:
            messages.error(request, "Resolution message is required.")
            return redirect(f"employee_complaint/{complaint_id}")
        
        # Update complaint
        complaint.status = 1  # Resolved
        complaint.resolution = resolution
        complaint.resolved_at = now()
        complaint.save()
        
        messages.success(request, "Complaint has been resolved successfully.")
    
    return redirect('resolve_complaints')

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
    # Get the product for which feedback is being submitted
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # Get the rating and review text from the POST data
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')

        # Ensure rating and review_text are provided
        if rating and review_text:
            # Create a new Feedback object and save it
            feedback = Feedback(
                product=product,
                user=request.user,  # Assuming the user is authenticated
                rating=rating,
                message=review_text
            )
            feedback.save()

            # Redirect to the product details page
            return redirect('product_details', product_id=product.id)

    # If it's a GET request or form is not valid, just render the page
    return render(request, 'product_details.html', {'product': product})

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
    # Retrieve the current user profile or create one if it doesn't exist
    u=request.session.get("id")

    try:
        user_profile = UserProfile.objects.get(id=u)
    except UserProfile.DoesNotExist:
        user_profile = None

    if request.method == 'POST':
        # Handling form submission for profile update
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        profile_picture = request.FILES.get('profile_picture')
        email = request.POST.get('email')

        # Update profile details
        if user_profile:
            user_profile.full_name = full_name
            user_profile.phone = phone
            if profile_picture:
                user_profile.profile_picture = profile_picture
            user_profile.save()
        else:
            UserProfile.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                profile_picture=profile_picture
            )

        # Update user email directly
        request.user.email = email
        request.user.save()

        # Handle password change form submission
        password = request.POST.get('password')
        if password:
            # Store the password as plain text (Not Recommended for production)
            request.user.password = password
            request.user.save()

        return redirect('profile_management')  # Redirect after successful update

    # Password change form (if needed, not necessary for plain text passwords)
    #password_form = PasswordChangeForm(request.user)

    return render(request, 'profile_management.html', {
        'user_profile': user_profile,
        'password_form': ProfileUpdateForm
    })

def change_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        user = request.user
        if user and new_password:
            user.password = new_password  # Not secure, use `set_password()`
            user.save()
            return redirect('profile_management')

    return render(request, 'change_password.html')

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

# ==============================
#     CHATBOT ASSISTANCE
# ==============================

# Sample default responses
DEFAULT_RESPONSES = {
    "rental policy": "You can rent items for up to 7 days. Late returns may incur additional charges.",
    "available sizes": "Our sizes range from XS to XXL. Check the size chart for details.",
}

def chatbot_view(request):
    if request.method == "POST":
        user_query = request.POST.get("user_query", "").strip()

        if not user_query:
            return JsonResponse({"response": "Please enter a valid question.", "recommendations": []})

        # Check if response already exists
        chat_entry, created = ChatbotQuery.objects.get_or_create(user=request.user, query=user_query)

        if not created and chat_entry.response:
            response = chat_entry.response
        else:
            # Assign a default response if applicable
            response = DEFAULT_RESPONSES.get(user_query.lower(), "I'm sorry, I don't have an answer for that yet.")
            chat_entry.response = response
            chat_entry.save()

        # Get product recommendations
        recommendations = []
        matching_products = Product.objects.filter(name__icontains=user_query)

        for product in matching_products:
            recommended_items = ProductRecommendation.objects.filter(product=product)
            recommendations.extend([rec.recommended_product.name for rec in recommended_items])

        return JsonResponse({"response": response, "recommendations": recommendations})

    return render(request, "chatbot.html")

# ==============================
#     OTHERS
# ==============================
def sustainability_impact(request):
    return render(request, "sustainability_impact.html")

def support_center(request):
    return render(request, "support_center.html")
