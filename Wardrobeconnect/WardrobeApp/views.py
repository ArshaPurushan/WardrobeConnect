from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.files.storage import default_storage
from django.utils.timezone import now
from .models import UserProfile, Login, Product, Category, Booking, Feedback, Complaint, Employee, Admin  
from .forms import ProductForm, EmployeeForm
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
        name = request.POST["name"]
        email = request.POST["email"]
        phone = request.POST["phone"]
        username = request.POST["username"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("user_register")

        if Login.objects.filter(Q(username=username) | Q(email=email)).exists():
            messages.error(request, "Username or Email already exists!")
            return redirect("user_register")

        login_instance = Login.objects.create(username=username, password=password, types="user", status=True)
        UserProfile.objects.create(logid=login_instance, name=name, email=email, phone=phone)

        messages.success(request, "Registration successful! You can now log in.")
        return redirect("login")

    return render(request, "user_register.html")

# Check if user is admin
def is_admin(user):
    return user.is_staff or user.is_superuser  # Restrict access to admins only

@login_required
@user_passes_test(is_admin)
def manage_users(request, status=None):
    """View to manage users based on their approval status."""
    
    # Validate status input
    valid_statuses = {"pending": 0, "approved": 1, "rejected": 2}
    
    if status not in valid_statuses:
        status = "pending"  # Default to pending users

    users = UserProfile.objects.filter(status=valid_statuses[status])
    
    return render(request, "manage_users.html", {"users": users, "status": status})

@login_required
@user_passes_test(is_admin)
def approve_user(request, user_id):
    """Approve a user by updating their status."""
    user = get_object_or_404(UserProfile, id=user_id)
    user.status = 1  # Approved
    user.save()
    messages.success(request, f"User '{user.name}' approved successfully!")
    return redirect("manage_users", status="pending")

@login_required
@user_passes_test(is_admin)
def reject_user(request, user_id):
    """Reject a user by updating their status and setting rejected flag."""
    user = get_object_or_404(UserProfile, id=user_id)
    user.status = 2  # Rejected
    user.save()
    messages.error(request, f"User '{user.name}' has been rejected.")
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

        # Check if user is in Admin table
        try:
            admin = Admin.objects.get(username=username)

            # Debugging: Print retrieved password
            print(f"Admin Found. Stored Password: {admin.password}")

            if admin.password == password:  # Plain text comparison
                request.session["username"] = admin.username
                request.session["user_type"] = "admin"
                messages.success(request, "Admin login successful!")
                return redirect("admin_dashboard")
            else:
                messages.error(request, "Invalid password.")
                return redirect("login")

        except Admin.DoesNotExist:
            print("Admin not found")  # Debugging
            pass  # Continue checking in Login model

        # Check if user exists in the Login model
        try:
            user = Login.objects.get(username=username)

            # Debugging: Print retrieved password
            print(f"User Found. Stored Password: {user.password}")

            if user.password == password:  # Plain text comparison
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
            print("User not found")  # Debugging
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")

# ==============================
#       DASHBOARDS
# ==============================

def admin_dashboard(request):
    return render(request, "admin_dashboard.html")

def employee_dashboard(request):
    return render(request, "employee_dashboard.html")

def customer_dashboard(request):
    products = Product.objects.all()
    return render(request, "customer_dashboard.html", {"products": products})

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

def employee_inventory(request):
    if "username" not in request.session or request.session["user_type"] != "employee":
        return redirect("login")

    username = request.session["username"]
    try:
        employee = Employee.objects.get(logid__username=username)
        products = Product.objects.all()  # Fetch all products
    except Employee.DoesNotExist:
        messages.error(request, "Unauthorized access!")
        return redirect("login")

    return render(request, "employee_inventory.html", {"products": products})


def employee_add_product(request):
    if "username" not in request.session or request.session["user_type"] != "employee":
        return redirect("login")

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        category = get_object_or_404(Category, id=category_id)

        Product.objects.create(
            category=category,
            name=name,
            price=price,
            stock=stock,
            description=description,
            image=image,
            availability="available",  # Default availability
        )
        messages.success(request, "Product added successfully!")
        return redirect("employee_inventory")

    categories = Category.objects.all()
    return render(request, "employee_add_product.html", {"categories": categories})


def delete_product(request, product_id):
    if "username" not in request.session or request.session["user_type"] != "employee":
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect("employee_inventory")

def update_availability(request, product_id):
    if "username" not in request.session or request.session["user_type"] != "employee":
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        availability = request.POST.get("availability")
        if availability in ["available", "rented", "returned"]:
            product.availability = availability
            product.save()
            messages.success(request, "Product availability updated successfully!")

    return redirect("employee_inventory")

# ==============================
#    SEARCH PRODUCT
# ==============================

def search_products(request):
    query = request.GET.get("query", "").strip()
    products = Product.objects.all()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(category__name__icontains=query))

    return render(request, "search_products.html", {"products": products, "query": query})


# ==============================
#    RENTAL & PAYMENT PROCESSING
# ==============================

def rent_product(request, product_id):
    if "username" not in request.session:
        return redirect("login")

    product = Product.objects.get(id=product_id)
    user = get_object_or_404(Login, username=request.session["username"])

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        rental_duration = int(request.POST.get("rental_duration", 1))
        total_price = product.price * quantity * rental_duration  

        booking = Booking.objects.create(
            user=user,
            product=product,
            quantity=quantity,
            rental_start_date=now(),
            rental_end_date=now() + timedelta(days=rental_duration),
            total_price=total_price,
            status="Pending"
        )

        return redirect("booking_confirmation", booking_id=booking.id)

    return render(request, "rent_product.html", {"product": product})

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "booking_confirmation.html", {"booking": booking})

def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == "POST":
        booking.status = "Paid"
        booking.save()
        messages.success(request, "Payment successful! Your rental is confirmed.")
        return redirect("customer_dashboard")

    return render(request, "payment_page.html", {"booking": booking})

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

def complaint(request):
    if request.method == "POST":
        user = get_object_or_404(Login, username=request.session["username"])
        complaint_text = request.POST.get("complaint")
        Complaint.objects.create(user=user, complaint_text=complaint_text)
        messages.success(request, "Complaint submitted successfully!")
        return redirect("customer_dashboard")

    return render(request, "complaint.html")


def trending_products(request):
    return render(request, "trending_products.html")

def resolve_complaints(request):
    return render(request, "reslove_complaints")

def view_reports(request):
    return render(request, "view_reports")


def chatbot_support(request):
    return render(request, "chatbot.html")


def about(request):
    return render(request, "about.html")

def services(request):
    return render(request, "services.html")

