from django import forms
from .models import Product
from .models import Employee
from .models import UserProfile
from .models import Booking

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'stock', 'description', 'image', 'availability']


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name','username', 'email', 'password', 'contact_number', 'position', 'status', 'profile_picture']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'email', 'phone','password']


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
