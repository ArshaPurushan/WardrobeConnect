from django import forms
from .models import  Login
from .models import Employee
from .models import UserProfile
from .models import Booking
from django.contrib.auth.forms import PasswordChangeForm
from .models import Product, ProductSize, ProductReview

SIZE_CHOICES = [("S", "Small"), ("M", "Medium"), ("L", "Large"), ("XL", "X-Large"), ("XXL", "XX-Large")]

class ProductForm(forms.ModelForm):
    sizes = forms.MultipleChoiceField(
        choices=SIZE_CHOICES,
        required=True,  # Ensure at least one size is selected
        widget=forms.CheckboxSelectMultiple
    )
    size_stock = forms.JSONField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Product
        fields = ["name", "category", "subcategory", "description", "price", "gender", "image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing a product, load existing size & stock data
        if self.instance.pk:
            existing_sizes = self.instance.sizes.values_list("size", flat=True)
            self.fields["sizes"].initial = list(existing_sizes)

            # Load stock data for each size
            size_stock_data = {
                size_obj.size: size_obj.stock for size_obj in self.instance.sizes.all()
            }
            self.fields["size_stock"].initial = size_stock_data

    def clean(self):
        cleaned_data = super().clean()
        selected_sizes = cleaned_data.get("sizes", [])
        size_stock_data = {}

        # Retrieve stock values dynamically for each selected size
        for size in selected_sizes:
            stock_key = f"stock_{size}"
            stock_value = self.data.get(stock_key)

            if stock_value and stock_value.isdigit():
                size_stock_data[size] = int(stock_value)
            else:
                size_stock_data[size] = 0  # Default stock to 0 if empty

        cleaned_data["size_stock"] = size_stock_data
        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)

        if commit:
            product.save()

            # Clear any old ProductSize associations before saving new data
            ProductSize.objects.filter(product=product).delete()

            # Save new sizes and stock information
            size_stock_data = self.cleaned_data.get("size_stock", {})
            for size, stock in size_stock_data.items():
                if stock > 0:  # Don't save sizes with 0 stock
                    ProductSize.objects.create(product=product, size=size, stock=stock)

            # Update total stock for the product based on all sizes
            total_stock = sum(size_stock_data.values())
            product.stock = total_stock
            product.save()

        return product


class EmployeeForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Password")

    class Meta:
        model = Employee
        fields = ["name", "position", "profile_picture"]
        widgets = {
            "position": forms.Select(choices=[
                (0, "General Staff"),
                (1, "Manager"),
                (2, "Delivery Staff")
            ]),
        }

    def save(self, commit=True):
        employee = super().save(commit=False)
        if not employee.user:
            user = Login.objects.create(
                email=self.cleaned_data["email"],
                password=self.cleaned_data["password"],  # Ideally, hash this
                types=2,  # Employee type
            )
            employee.user = user
        if commit:
            employee.save()
        return employee



class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = UserProfile
        fields = ['full_name', 'phone', 'profile_picture']

    def save(self, commit=True):
        user_profile = super().save(commit=False)
        login_user = user_profile.user  # Get the related Login model

        # Update email and password in the Login model
        if self.cleaned_data.get("email"):
            login_user.email = self.cleaned_data["email"]
        
        if self.cleaned_data.get("password"):
            login_user.password = self.cleaned_data["password"]  # Store plain text password directly

        if commit:
            login_user.save()
            user_profile.save()

        return user_profile



class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["address", "rental_duration"]  # ✅ Let user enter delivery address & rental period
    
    rental_duration = forms.IntegerField(
        min_value=1, 
        initial=7,  # Default rental period of 7 days
        help_text="Enter rental duration in days."
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Enter your delivery address"}), 
        required=True
    )

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'review']
