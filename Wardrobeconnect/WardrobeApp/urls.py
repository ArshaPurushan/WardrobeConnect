from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from . import views



urlpatterns = [
    
    #         MAIN PAGES
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),

 
    #       AUTHENTICATION
    path("login/", views.login_view, name="login"),
    path("user_register/", views.user_register, name="user_register"),


    #       DASHBOARD ROUTES
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("employee_dashboard/", views.employee_dashboard, name="employee_dashboard"),
    path("customer_dashboard/", views.customer_dashboard, name="customer_dashboard"),


    #       USER MANAGEMENT
    path("manage-users/", views.manage_users, name="manage_users"),
    path("manage-users/<str:status>/", views.manage_users, name="manage_users"),
    path("approve-user/<int:user_id>/", views.approve_user, name="approve_user"),
    path("reject-user/<int:user_id>/", views.reject_user, name="reject_user"),
    
    # Employee Management
    path('manage_employees/', views.manage_employees, name='manage_employees'),
    path('add_employee/', views.add_employee, name='add_employee'),
    path('edit_employee/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('delete_employee/<int:employee_id>/', views.delete_employee, name='delete_employee'),
   
    #   INVENTORY MANAGEMENT (admin)
    path("admin_manage-inventory/", views.admin_manage_inventory, name="admin_manage_inventory"),
    path("admin_manage-inventory/approve/<int:product_id>/", views.approve_product, name="approve_product"),
    path("admin_manage-inventory/reject/<int:product_id>/", views.reject_product, name="reject_product"),
    #path("admin_manage-inventory/edit/<int:product_id>/", views.edit_product, name="edit_product"),
    #path("admin_manage-inventory/delete/<int:product_id>/", views.delete_product, name="delete_product"),


    #   INVENTORY MANAGEMENT (admin)
    path("employee_inventory/", views.employee_inventory, name="employee_inventory"),
    path("employee_add_product/", views.employee_add_product, name="employee_add_product"),
    path("delete_product/<int:product_id>/", views.delete_product, name="delete_product"),
    path("update_availability/<int:product_id>/", views.update_availability, name="update_availability"),



    #     PRODUCT LISTING & SEARCH
    path("search/", views.search, name="search"),
    path("trending_products/", views.trending_products, name="trending_products"),

     #     PRODUCT VIEW & CART
    path('product_details/<int:product_id>/', views.product_details, name='product_details'),
    path("check_availability/<int:product_id>/", views.check_availability, name="check_availability"),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('clear_cart/', views.clear_cart, name='clear_cart'),

    #       CHECKOUT
    path("checkout/", views.checkout, name="checkout"),
    path("invoice/", views.invoice, name="invoice"),  # ✅ Invoice Page
    path("payment_page/<int:booking_id>/", views.payment_page, name="payment_page"),
    path("confirm_order/<int:booking_id>/", views.confirm_order, name="confirm_order"),
    path("order_history/", views.order_history, name="order_history"),


    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),



    #    RENTAL & PAYMENT PROCESSING
    path("rent/<int:product_id>/", views.rent_product, name="rent_product"),
    #path("booking/confirmation/<int:booking_id>/", views.booking_confirmation, name="booking_confirmation"),
    #path("payment_page/<int:booking_id>/", views.payment_page, name="payment_page"),  # ✅ Ensure it expects booking_id
    #path("confirm_order/<int:booking_id>/", views.confirm_order, name="confirm_order"),


    #   FEEDBACK & COMPLAINTS (ADMIN & EMPLOYEE)
    #path("feedback/submit/", views.feedback, name="feedback"),
    #path("complaint/submit/", views.complaint, name="complaint"),
    path("admin_resolve_complaints/", views.admin_resolve_complaints, name="admin_resolve_complaints"),  
    path("reply_complaint/<int:complaint_id>/", views.reply_complaint, name="reply_complaint"),
    path("employee_complaints/", views.employee_complaints, name="employee_complaints"),
    path("resolve_complaints/<int:complaint_id>/", views.resolve_complaints, name="resolve_complaints"),
    


    #    RENTAL HISTROY
    path('rental-history/', views.rental_history, name='rental_history'),

    #   PROFILE MANAGEMENT
    path('profile-management/', views.profile_management, name='profile_management'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),


    #   FEEDBACK & COMPLAINTS (CUSTOMER)
    path("feedback/submit/", views.feedback, name="feedback"),
    path("complaint/submit/", views.complaint, name="complaint"),

    

    #        CHATBOT SUPPORT
    path("chatbot", views.chatbot, name="chatbot"),


    #         REPORTS
     path('view_reports/', views.view_reports, name='view_reports'),
    path('view_reports/<int:report_id>/', views.update_report_status, name='update_report_status'),
    path("financial_reports/", views.financial_reports, name="financial_reports"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Serve media files in development
#if settings.DEBUG:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)