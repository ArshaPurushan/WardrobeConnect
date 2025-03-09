from django import forms
from .models import Product
from .models import Employee

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "price", "stock", "description", "image", "availability"]




class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name','username', 'email', 'password', 'contact_number', 'position', 'status', 'profile_picture']