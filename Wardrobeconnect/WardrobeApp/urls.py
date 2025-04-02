from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from . import views # Ensure views are correctly imported


urlpatterns = [
    #         MAIN PAGES
    path("", views.index, name="index"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

   
    #       DASHBOARD ROUTES
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("employee_dashboard/", views.employee_dashboard, name="employee_dashboard"),
    path("customer_dashboard/", views.customer_dashboard, name="customer_dashboard"),


    #         USER REGISTRATION
    path('register/', views.register, name='register'),

    
    #         USER MANAGEMENT
    path('manage-users/', views.manage_users, name='manage_users'),  # Default view
    path('manage-users/<str:status>/', views.manage_users, name='manage_users_with_status'),
    path('report_user/<int:user_id>/', views.report_user, name='report_user'),
    path('block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('activate_user/<int:user_id>/', views.activate_user, name='activate_user'),

    #         EMPLOYEE MANAGEMENT
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

    #   INVENTORY MANAGEMENT (employee)
    path("employee_inventory/", views.employee_inventory, name="employee_inventory"),
    path("employee_add_product/", views.add_product, name="employee_add_product"),
    path("employee_edit_product/<int:product_id>/", views.edit_product, name="employee_edit_product"),  # For editing
    #path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path("delete_product/<int:product_id>/", views.delete_product, name="delete_product"),
    path("update_availability/<int:product_id>/", views.update_availability, name="update_availability"),


    #       SEARCH
    path('search/', views.search, name='search'),
    path("product_details/<int:product_id>/", views.product_details, name="product_details"), 

    #       CART
    path('cart/', views.cart, name='cart'),
    path('add_to_cart/<int:product_id>/<int:size_id>/', views.add_to_cart, name='add_to_cart'),
    path("remove_from_cart/<int:cart_id>/", views.remove_from_cart, name="remove_from_cart"),

    path('update_cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('clear_cart/', views.clear_cart, name='clear_cart'),


    path("checkout/", views.checkout, name="checkout"),


    path("payment_page/<int:booking_id>/", views.payment_page, name="payment_page"),
    path("confirm_order/<int:booking_id>/", views.confirm_order, name="confirm_order"),


    path("invoice/<int:booking_id>/", views.invoice, name="invoice"),
    path("rental-history/", views.rental_history, name="rental_history"),

    

    #       WISHlist
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/add/<int:product_id>/", views.add_to_wishlist, name="add_to_wishlist"),
    path("wishlist/remove/<int:product_id>/", views.remove_from_wishlist, name="remove_from_wishlist"),
    path('wishlist/add-to-cart/<int:product_id>/', views.add_to_cart_from_wishlist, name='add_to_cart_from_wishlist'),



    path("admin_payment/", views.admin_payment, name="admin_payment"),  # ✅ Added admin_payment

    path("employee_bookings/", views.employee_bookings, name="employee_bookings"),


    path("complaints/", views.complaints, name="complaints"),


     #   Review
    path('product_details/<int:product_id>/', views.product_details, name='product_details'),
    path('product/<int:product_id>/feedback/', views.submit_feedback, name='feedback'),

    #   COMPLAINT MANAGEMENT (admin)
    path("admin_resolve_complaints/", views.admin_resolve_complaints, name="admin_resolve_complaints"),  
    path("reply_user_complaint/<int:complaint_id>/", views.reply_user_complaint, name="reply_user_complaint"),

    #   COMPLAINT MANAGEMENT (employee)
    path("employee_complaints/", views.employee_complaints, name="employee_complaints"),
    path("resolve_complaints/<int:complaint_id>/", views.resolve_complaints, name="resolve_complaints"),



     #   REPORT MANAGEMENT (admin)
    path('reports/', views.view_reports, name='view_reports'),
    path('reports/approve/<int:report_id>/', views.approve_report, name='approve_report'),
    path('reports/reject/<int:report_id>/', views.reject_report, name='reject_report'),
    path('admin/generate_report/', views.generate_admin_report, name='generate_admin_report'),
    path('export/reports/pdf/', views.export_reports_pdf, name='export_reports_pdf'),
    #path('export/reports/excel/', views.export_reports_excel, name='export_reports_excel'),

     #   REPORT MANAGEMENT (employee)
    path("employee_reports/", views.employee_reports, name="employee_reports"),

    #   PROFILE MANAGEMENT
    path('profile_management/', views.profile_management, name='profile_management'),
    path('change_password/', views.change_password, name='change_password'),

    #   RENTAL HISTROY MANAGEMENT
    path('rental_history/', views.rental_history, name='rental_history'),

    #   CHATBOT
    path("chatbot/", views.chatbot_view, name="chatbot"),

    #   OTHERS
    path('sustainability-impact/', views.sustainability_impact, name='sustainability_impact'),
    path('support-center/', views.support_center, name='support_center'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
