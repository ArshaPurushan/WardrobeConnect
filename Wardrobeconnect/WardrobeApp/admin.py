from django.contrib import admin
from .models import Employee

# Register your models here.
admin.site.register(Employee)

from django.contrib import admin
from .models import Product  # Import the Product model

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "availability")  # Fields to display
    search_fields = ("name", "category__name")  # Enable search by product name and category
    list_filter = ("availability", "category")  # Add filters for better navigation
    ordering = ("-id",)  # Sort by newest products first

# If Category is not registered, register it as well
#from .models import Category
#admin.site.register(Category)
