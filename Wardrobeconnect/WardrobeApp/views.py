import logging
import razorpay
from razorpay.errors import BadRequestError, ServerError, SignatureVerificationError

from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import json
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.core.files.storage import default_storage
from django.utils.timezone import now
from .models import UserProfile, Login, Product, Booking, Feedback, Complaint, Employee, Admin ,Rental,SalesReport, ChatbotResponse, Cart, Wishlist, Payment
from .forms import ProductForm, EmployeeForm, ProfileUpdateForm, CheckoutForm

import random
from django.conf import settings
import os


# ==============================
#         HOME PAGE
# ==============================
def index(request):
    return render(request, "index.html")

# ==============================
#    USER REGISTRATION & LOGIN
# ==============================

def user_register(request):
    if request.method == "POST":
        print("Received POST Data:", request.POST)  # Debugging

        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        print(f"Checking Username: {username}")
        print(f"Checking Email: {email}")

        if not username:
            messages.error(request, "Username cannot be empty!")
            return redirect("user_register")

        if Login.objects.filter(Q(username=username) | Q(email=email)).exists():
            messages.error(request, "Username or Email already exists!")
            return redirect("user_register")

        login_instance = Login.objects.create(username=username, password=password, types="user", status=True)
        UserProfile.objects.create(user=login_instance, full_name=name, email=email, phone=phone, password=password)

        messages.success(request, "Registration successful! You can now log in.")
        return redirect("login")

    return render(request, "user_register.html")




# Check if the user exists in the Admin table
def is_admin(user):
    return Admin.objects.filter(username=user.username).exists()

@login_required
@user_passes_test(is_admin)
def manage_users(request, status="pending"):
    """View to manage users based on their approval status."""
    
    # Define valid status mappings
    status_mapping = {"pending": 0, "approved": 1, "rejected": 2}
    
    # Ensure provided status is valid
    if status not in status_mapping:
        status = "pending"  # Default to pending users

    users = UserProfile.objects.filter(status=status_mapping[status])
    
    return render(request, "manage_users.html", {"users": users, "status": status})

@login_required
@user_passes_test(is_admin)
def approve_user(request, user_id):
    """Approve a user by updating their status."""
    user = get_object_or_404(UserProfile, id=user_id)
    
    if user.status == 1:
        messages.info(request, f"User '{user.full_name}' is already approved.")
    else:
        user.status = 1  # Approved
        user.save()
        messages.success(request, f"User '{user.full_name}' approved successfully!")
    
    return redirect("manage_users", status="pending")

@login_required
@user_passes_test(is_admin)
def reject_user(request, user_id):
    """Reject a user by updating their status."""
    user = get_object_or_404(UserProfile, id=user_id)
    
    if user.status == 2:
        messages.info(request, f"User '{user.full_name}' is already rejected.")
    else:
        user.status = 2  # Rejected
        user.save()
        messages.error(request, f"User '{user.full_name}' has been rejected.")
    
    return redirect("manage_users", status="pending")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, "Both username and password are required!")
            return redirect("login")

        # Debugging: Print username and password (Remove in production)
        print(f"Trying to log in with Username: {username}, Password: {password}")

        # Check Admin Table
        try:
            admin = Admin.objects.get(username=username)
            if admin.password == password:  # Plain text comparison
                request.session["username"] = admin.username
                request.session["user_type"] = "admin"
                messages.success(request, "Admin login successful!")
                return redirect("admin_dashboard")
            else:
                messages.error(request, "Invalid password.")
                return redirect("login")
        except Admin.DoesNotExist:
            pass  # Continue checking other tables

        # Check Login Table
        try:
            user = Login.objects.get(username=username)
            if user.password == password:  # Plain text comparison
                try:
                    profile = UserProfile.objects.get(user=user)
                    if profile.status == 0:
                        messages.error(request, "Your account is pending approval.")
                        return redirect("login")
                    elif profile.status == 2:
                        messages.error(request, "Your account has been rejected.")
                        return redirect("login")
                except UserProfile.DoesNotExist:
                    messages.error(request, "User profile not found.")
                    return redirect("login")

                request.session["username"] = user.username
                request.session["user_type"] = user.types
                messages.success(request, f"{user.types.capitalize()} login successful!")
                if user.types == "admin":
                    return redirect("admin_dashboard")
                elif user.types == "employee":
                    return redirect("employee_dashboard")
                elif user.types == "user":
                    return redirect("customer_dashboard")
            else:
                messages.error(request, "Invalid password.")
                return redirect("login")
        except Login.DoesNotExist:
            pass  # Continue checking Employee table

        # Check Employee Table
        try:
            employee = Employee.objects.get(username=username)
            if employee.password == password:  # Plain text comparison
                request.session["username"] = employee.username
                request.session["user_type"] = "employee"
                messages.success(request, "Employee login successful!")
                return redirect("employee_dashboard")
            else:
                messages.error(request, "Invalid password.")
                return redirect("login")
        except Employee.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")


# ==============================
#       DASHBOARDS
# ==============================

def admin_dashboard(request):
    return render(request, "admin_dashboard.html")

@login_required
def employee_dashboard(request):
    user_type = request.session.get("user_type")  # Get user type from session
    print("User Type:", user_type)  # Debugging output

    if user_type != "employee":
        return redirect("login")  # Restrict access if not an employee

    return render(request, "employee_dashboard.html")  # Render dashboard template

@login_required
def customer_dashboard(request):
    username = request.session.get("username")
    user_type = request.session.get("user_type")

    if not username or user_type != "user":
        messages.error(request, "Unauthorized access!")
        return redirect("login")

    try:
        user = Login.objects.get(username=username)  # Fetch user
    except Login.DoesNotExist:
        messages.error(request, "User not found!")
        return redirect("login")

    # Fetch available products and rented items
    products = Product.objects.filter(availability="available")
    rented_products = Rental.objects.filter(customer=user, status="rented")

    context = {
        "products": products,
        "rented_products": rented_products,
    }
    return render(request, "customer_dashboard.html", context)


# ==============================
#    EMPLOYEE MANAGEMENT
# ==============================

def manage_employees(request):
    employees = Employee.objects.all()
    return render(request, 'manage_employees.html', {'employees': employees})

def add_employee(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES)  # Handle images
        if form.is_valid():
            form.save()
            return redirect('manage_employees')
    else:
        form = EmployeeForm()
    
    return render(request, 'add_employee.html', {'form': form})

def edit_employee(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('manage_employees')
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'edit_employee.html', {'form': form})

def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    employee.delete()
    messages.success(request, "Employee deleted successfully!")
    return redirect('manage_employees')


# ==============================
#    PRODUCT MANAGEMENT (admin)
# ==============================

def admin_manage_inventory(request):
    products = Product.objects.all()
    return render(request, 'admin_manage_inventory.html', {'products': products})

def approve_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.status = "approved"
    product.save()
    return redirect('admin_manage_inventory')

def reject_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.status = "rejected"
    product.save()
    return redirect('admin_manage_inventory')


# ==============================
#    PRODUCT MANAGEMENT (employee)
# ==============================

# Configure logger
logger = logging.getLogger(__name__)

def employee_inventory(request):
    """ Display inventory and handle product addition. """
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully!")
            return redirect("employee_inventory")  # Redirect to prevent duplicate submission
        else:
            messages.error(request, "Invalid form submission. Please check your inputs.")

    else:
        form = ProductForm()

    products = Product.objects.all()  # Fetch all products for display
    return render(request, "employee_inventory.html", {"form": form, "products": products})


def employee_add_product(request):
    """ Allow employees to add new products dynamically. """
    if request.session.get("user_type") != "employee":
        messages.error(request, "Access Denied: Only employees can add products.")
        return redirect("login")

    CATEGORY_CHOICES = Product.CATEGORY_CHOICES  # Get category choices from the model

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", "").strip().lower()
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        description = request.POST.get("description", "").strip()
        image = request.FILES.get("image")

        # Validate required fields
        if not name or not category or not price or not stock:
            messages.error(request, "All fields except image are required.")
            return redirect("employee_add_product")

        # Validate category choice
        valid_categories = dict(Product.CATEGORY_CHOICES).keys()
        if category not in valid_categories:
            messages.error(request, "Invalid category selection.")
            return redirect("employee_add_product")

        # Convert price and stock to correct data types
        try:
            price = float(price)
            stock = int(stock)
            if price < 0 or stock < 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Invalid price or stock value! Ensure they are positive numbers.")
            return redirect("employee_add_product")

        # Create and save the product
        new_product = Product.objects.create(
            category=category,
            name=name,
            price=price,
            stock=stock,
            description=description,
            image=image if image else None,
            availability="available",
        )

        messages.success(request, f"Product '{new_product.name}' added successfully!")
        return redirect("employee_inventory")

    return render(request, "employee_add_product.html", {"CATEGORY_CHOICES": CATEGORY_CHOICES})

def delete_product(request, product_id):
    """ Allow employees to delete a product (via POST request only). """
    if request.session.get("user_type") != "employee":
        messages.error(request, "Access Denied: Only employees can delete products.")
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully!")
        logger.info(f"Product '{product_name}' deleted by employee.")

    return redirect("employee_inventory")


def update_availability(request, product_id):
    """ Allow employees to update product availability. """
    if request.session.get("user_type") != "employee":
        messages.error(request, "Access Denied: Only employees can update availability.")
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        availability = request.POST.get("availability")

        valid_statuses = [key for key, _ in Product.AVAILABILITY_CHOICES]

        if availability in valid_statuses:
            product.availability = availability
            product.save()
            messages.success(request, f"Product availability updated to '{availability}'.")
            logger.info(f"Availability for product '{product.name}' updated to '{availability}'.")
        else:
            messages.error(request, f"Invalid availability status. Choose from: {', '.join(valid_statuses)}")

    return redirect("employee_inventory")

# ==============================
#    SEARCH PRODUCT
# ==============================

def search(request):
    query = request.GET.get('q', '').strip()

    if query:
        if query.isdigit():  # If user searches by price (numeric input)
            products = Product.objects.filter(price__lte=query)  # Less than or equal to
        else:
            products = Product.objects.filter(
                Q(name__icontains=query) | 
                Q(category__icontains=query)
            )
    else:
        products = Product.objects.all()

    # Handle AJAX request for real-time search
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
        product_list = [
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": str(product.price),
                "image": product.image.url if product.image else None  # Handle missing image
            }
            for product in products
        ]
        return JsonResponse({"products": product_list})

    return render(request, 'search.html', {'products': products})


# ==============================
#    PRODUCT DETAILS 
# ==============================

def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_details.html', {'product': product})


# ==============================
#    CHECK AVAILABILITY
# ==============================

@login_required
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

        # Check if stock is available
        if product.stock < quantity:
            return JsonResponse({"error": "Not enough stock available"}, status=400)

        # Add to cart
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            size=size,
            rental_start_date=rental_start_date,
            rental_end_date=rental_end_date,
            defaults={"quantity": quantity},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return JsonResponse({"message": "Product added to cart", "cart_id": cart_item.id}, status=200)
    

# ==============================
#     CART
# ==============================


#     ADD TO CART
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # ✅ Fetch correct user from session
    username = request.session.get("username")  
    user = get_object_or_404(Login, username=username)  

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            messages.error(request, "Quantity must be at least 1.")
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        # ✅ Ensure one cart item per product per user (increase quantity if already in cart)
        cart_item, created = Cart.objects.get_or_create(user=user, product=product)
        if not created:
            cart_item.quantity += quantity  # Increase quantity instead of overwriting
        else:
            cart_item.quantity = quantity  # Set quantity for new items
        cart_item.save()

        messages.success(request, f"{product.name} added to cart!")

    except IntegrityError:
        messages.error(request, "Error adding product to cart.")

    # ✅ Redirect back to product page instead of forcing cart view
    return redirect(request.META.get('HTTP_REFERER', 'cart'))



#     VIEW CART
@login_required
def cart(request):
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

    cart_items = Cart.objects.filter(user=user)

    for item in cart_items:
        item.total_price = item.quantity * item.product.price

    grand_total = sum(item.quantity * item.product.price for item in cart_items)  # ✅ Fixed total price calculation

    return render(request, 'cart.html', {'cart_items': cart_items, 'grand_total': grand_total})



#     REMOVE FROM CART
@login_required
def remove_from_cart(request, product_id):
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

    cart_item = get_object_or_404(Cart, user=user, product_id=product_id)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")

    return redirect('cart')



#     UPDATE CART (WITH AJAX)
@login_required
def update_cart(request, product_id):
    if request.method == "POST":
        try:
            new_quantity = int(request.POST.get('quantity', 1))

            username = request.session.get("username")
            user = get_object_or_404(Login, username=username)

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
@login_required
def clear_cart(request):
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

    Cart.objects.filter(user=user).delete()
    messages.success(request, "Your cart has been cleared.")

    return redirect('cart')



#     MOVE TO WISHLIST
@login_required
def move_to_wishlist(request, product_id):
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

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


#    VIEW WISHLIST
def wishlist(request):
    wishlist = request.session.get('wishlist', {})
    return render(request, 'wishlist.html', {'wishlist_items': wishlist})


#    ADD TO WISHLIST
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if created:
        messages.success(request, f"{product.name} added to wishlist! ✅")
    else:
        messages.info(request, f"{product.name} is already in your wishlist! ℹ️")

    return redirect('wishlist')


#    REMOVE FROM WISHLIST
def remove_from_wishlist(request, product_id):
    wishlist = request.session.get('wishlist', {})

    if str(product_id) in wishlist:
        del wishlist[str(product_id)]
        request.session['wishlist'] = wishlist
        request.session.modified = True  # Ensures session updates are saved
        messages.success(request, "Item removed from wishlist 🗑️.")
    else:
        messages.warning(request, "Item not found in wishlist! ⚠️")

    return redirect('wishlist')


# ==============================
#    INVOICE
# ==============================
from django.urls import reverse
@login_required
def invoice(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # 🔹 Delay redirect to order history by a few seconds
    response = render(request, "invoice.html", {"booking": booking})
    
    # After viewing the invoice, redirect to order history
    response["Refresh"] = "5; url=" + request.build_absolute_uri(reverse("order_history"))
    
    return response

# ==============================
#    CHECKOUT
# ==============================

#@login_required
from decimal import Decimal

def checkout(request):
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

    cart_items = Cart.objects.filter(user=user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    # 🔥 Calculate Total Price
    total_price = sum(Decimal(str(item.quantity)) * Decimal(str(item.product.price)) for item in cart_items)

    # 🔥 Dynamic Security Deposit (Set 10% of subtotal)
    security_deposit = total_price * Decimal("0.10")  
    total_with_deposit = total_price + security_deposit

    # 🔥 Ensure Booking Exists
    first_cart_item = cart_items.first()
    if first_cart_item:
        booking, created = Booking.objects.get_or_create(
            user=user, 
            status="Pending",
            defaults={"total_price": total_with_deposit, "product": first_cart_item.product}
        )
        if not created:
            booking.total_price = total_with_deposit
            booking.save()
    else:
        booking = None  

    return render(request, "checkout.html", {
        "cart_items": cart_items,
        "subtotal": total_price,  # ✅ Ensure subtotal is passed
        "security_deposit": security_deposit,  
        "grand_total": total_with_deposit,  # ✅ Ensure grand total is passed
        "booking": booking
    })

# ==============================
#    ORDER HISTORY
# ==============================

@login_required
def order_history(request):
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

    # ✅ Fetch only "Paid" bookings for this user
    bookings = Booking.objects.filter(user=user, status="Paid").order_by("-rental_start_date")

    return render(request, "order_history.html", {"bookings": bookings})


# ==============================
#    RENTAL & PAYMENT PROCESSING
# ==============================

@login_required
def rent_product(request, product_id):
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

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
                status="Pending"
            )

            messages.success(request, "Rental request submitted! Proceed to payment.")
            return redirect("booking_confirmation", booking_id=booking.id)

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("rent_product", product_id=product.id)

    return render(request, "rent_product.html", {"product": product})


@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "booking_confirmation.html", {"booking": booking})


# ==============================
#    PAYMENT PROCESSING (RAZORPAY)
# ==============================

def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))

        # 🏷️ Convert total price + deposit to paise (Razorpay requires amounts in paise)
        amount_in_paise = int((booking.total_price + booking.security_deposit) * 100)

        # 🏷️ Create Razorpay order
        payment_order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": 1,  # Auto-capture the payment
        })

        # 🏷️ Store order ID in session
        request.session["razorpay_order_id"] = payment_order["id"]

        return render(request, "payment_page.html", {
            "booking": booking,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "payment_order": payment_order
        })

    except (BadRequestError, ServerError) as e:
        messages.error(request, f"Payment setup failed: {str(e)}")
        return redirect("checkout")

@login_required
def confirm_order(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        razorpay_order_id = request.session.get("razorpay_order_id")
        payment_id = request.POST.get("razorpay_payment_id")
        signature = request.POST.get("razorpay_signature")

        if not razorpay_order_id or not payment_id or not signature:
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect("payment_page", booking_id=booking.id)

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
            
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            # ✅ Verify payment signature
            client.utility.verify_payment_signature(params_dict)

            # ✅ Update booking status
            booking.status = "Confirmed"
            booking.save()

            # ✅ Clear session data after successful transaction
            del request.session["razorpay_order_id"]

            messages.success(request, "Payment successful! Your booking is confirmed.")
            #return redirect("booking_success", booking_id=booking.id)
        
            # 🔹 Redirect to invoice page first, then order history
            return redirect("invoice", booking_id=booking.id)

        except SignatureVerificationError:
            messages.error(request, "Payment verification failed. Please try again.")
            return redirect("payment_page", booking_id=booking.id)

    return redirect("checkout")

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
#     FEEDBACK & COMPLAINTS
# ==============================
def feedback(request):
    if request.method == "POST":
        user = get_object_or_404(Login, username=request.session["username"])
        message = request.POST.get("message")
        Feedback.objects.create(user=user, message=message)
        messages.success(request, "Feedback submitted successfully!")
        return redirect("customer_dashboard")

    return render(request, "feedback.html")

# ==============================
#    CUSTOMER COMPLAINT SUBMISSION
# ==============================
@login_required
def complaint(request):
    """Allow customers to submit complaints."""
    username = request.session.get("username")

    if not username:
        messages.error(request, "You need to log in to submit a complaint.")
        return redirect("login")

    user = get_object_or_404(Login, username=username)

    if request.method == "POST":
        complaint_text = request.POST.get("complaint", "").strip()

        if not complaint_text:
            messages.error(request, "Complaint cannot be empty.")
            return redirect("customer_dashboard")

        Complaint.objects.create(customer=user, complaint_text=complaint_text, status="Pending")  # ✅ Ensure complaint is "Pending"
        messages.success(request, "Complaint submitted successfully!")
        return redirect("customer_dashboard")

    return render(request, "complaint.html")


# ==============================
#    EMPLOYEE VIEW OF COMPLAINTS
# ==============================
@login_required
def employee_complaints(request):
    """Employees can view all pending complaints."""
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

    # ✅ Ensure only employees can access this view
    if user.types != "employee":
        messages.error(request, "Access denied.")
        return redirect("customer_dashboard")

    complaints = Complaint.objects.filter(status="Pending").order_by("-created_at")
    return render(request, "employee_complaints.html", {"complaints": complaints})


# ==============================
#    EMPLOYEE RESOLVES COMPLAINT
# ==============================
@login_required
def resolve_complaint(request, complaint_id):
    """Allow an employee to resolve a complaint with an optional reply."""
    username = request.session.get("username")
    user = get_object_or_404(Login, username=username)

    # ✅ Ensure only employees can resolve complaints
    if user.types != "employee":
        messages.error(request, "Access denied.")
        return redirect("customer_dashboard")

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        reply_text = request.POST.get("reply", "").strip()

        if complaint.status == "Resolved":
            messages.warning(request, "This complaint is already resolved.")
        else:
            complaint.status = "Resolved"
            complaint.reply = reply_text if reply_text else "Resolved without a reply"
            complaint.save()
            messages.success(request, "Complaint resolved successfully!")

        return redirect("employee_complaints")

    return render(request, "resolve_complaints.html", {"complaint": complaint})

# ==============================
#     RENTAL HISTORY
# ==============================

def rental_history(request):
    if "username" not in request.session:
        messages.error(request, "You must be logged in to view your rental history.")
        return redirect("login")
    
    user = get_object_or_404(Login, username=request.session["username"])
    rentals = Booking.objects.filter(user=user).order_by("-rental_start_date")
    return render(request, "rental_history.html", {"rentals": rentals})

# ==============================
#     CHATBOT ASSISTANCE
# ==============================

# Predefined responses
RESPONSES = {
    "How can I rent a product?": "Go to the product page, select the quantity and duration, and click rent.",
    "How do I make a payment?": "After booking, go to the payment page and follow the instructions.",
    "What if my payment fails?": "Try again or contact support for assistance.",
    "How can I return my rental?": "Schedule a return via your order history page.",
    "Where is my order?": "Track your order status in the 'My Orders' section.",
}

def chatbot(request):
    if request.method == "POST":
        user_query = request.POST.get("user_query", "").strip()

        # Check if question already exists in the database
        chat_entry, created = ChatbotResponse.objects.get_or_create(question=user_query)

        if not created and chat_entry.response:
            response = chat_entry.response
        else:
            # Provide default response or escalate
            response = RESPONSES.get(user_query, "I'm sorry, I don't understand that question. An admin will review it.")
            chat_entry.response = response

            # Mark as escalated if response is generic
            if response.startswith("I'm sorry"):
                chat_entry.is_escalated = True

            chat_entry.save()

        return JsonResponse({"response": response})
    
    return render(request, "chatbot.html")



# ==============================
#     REPORTS
# ==============================
def view_reports(request):
    return render(request, "view_reports")

@login_required
def financial_reports(request):
    reports = SalesReport.objects.all()
    return render(request, "financial_reports.html", {"reports": reports})

# ==============================
#     OTHERS
# ==============================
def about(request):
    return render(request, "about.html")

def services(request):
    return render(request, "services.html")


# ==============================
#     RENTAL HISTROY
# ==============================

@login_required
def rental_history(request):
    rentals = Rental.objects.filter(user=request.user)
    return render(request, 'rental_history.html', {'rentals': rentals})

# ==============================
#     PROFILE MANAGEMENT
# ==============================

@login_required
def profile_management(request):
    user_profile = get_object_or_404(UserProfile, username=request.session.get('user'))  # Fetch UserProfile
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile_management')
    else:
        form = ProfileUpdateForm(instance=user_profile)

    return render(request, 'profile_management.html', {'form': form, 'user_profile': user_profile})


@login_required
def edit_profile(request):
    username = request.session.get('user')
    user_profile = get_object_or_404(UserProfile, username=username)

    if request.method == "POST":
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')

        user_profile.full_name = full_name  # Updating full_name instead of name
        user_profile.email = email
        user_profile.phone = phone
        user_profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('customer_dashboard')

    return render(request, 'edit_profile.html', {'user_profile': user_profile})


@login_required
def change_password(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)  # Get user profile

    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match!")
            return redirect('change_password')

        user = user_profile.user  # Get the associated User model instance
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect!")
            return redirect('change_password')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)  # Keeps the user logged in
        messages.success(request, "Password updated successfully!")
        return redirect('customer_dashboard')

    return render(request, 'change_password.html', {'user_profile': user_profile})


def trending_products(request):
    return render(request, "trending_products.html")


#   ADMIN RESOLVE COMPLAINT
def admin_resolve_complaints(request):
    complaints = Complaint.objects.all()
    return render(request, 'admin_resolve_complaints.html', {'complaints': complaints})

def reply_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == "POST":
        complaint.reply = request.POST.get("reply")  # Assuming a reply field
        complaint.save()
        return redirect("admin_resolve_complaints")  
    return render(request, "reply_complaint.html", {"complaint": complaint})

def resolve_complaints(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        complaint.status = "Resolved"
        complaint.save()
        return redirect('admin_resolve_complaints')  # Redirect back to admin page
    return render(request, 'resolve_complaints.html', {'complaint': complaint})


# ==============================
#     REPORT
# ==============================

# 📌 Get all reports
def view_reports(request):
    reports = SalesReport.objects.all()  # Fetch all reports
    return render(request, 'view_reports.html', {'reports': reports})

# 📌 Approve or Reject a Report
@csrf_exempt
def update_report_status(request, report_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get("status")

            if status not in ["approved", "rejected"]:
                return JsonResponse({'error': 'Invalid status'}, status=400)

            report = SalesReport.objects.get(id=report_id)
            report.report_status = status
            report.save()

            return JsonResponse({'message': f'Report {status} successfully'})
        except SalesReport.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)