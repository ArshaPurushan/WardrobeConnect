from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # ==============================
    #         MAIN PAGES
    # ==============================
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),

    # ==============================
    #       AUTHENTICATION
    # ==============================
    path("login/", views.login_view, name="login"),
    path("user_register/", views.user_register, name="user_register"),

    # ==============================
    #       DASHBOARD ROUTES
    # ==============================
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("employee_dashboard/", views.employee_dashboard, name="employee_dashboard"),
    path("customer_dashboard/", views.customer_dashboard, name="customer_dashboard"),

    # ==============================
    #       USER MANAGEMENT
    # ==============================
    path("manage-users/", views.manage_users, name="manage_users"),
    path("manage-users/<str:status>/", views.manage_users, name="manage_users"),
    path("approve-user/<int:user_id>/", views.approve_user, name="approve_user"),
    path("reject-user/<int:user_id>/", views.reject_user, name="reject_user"),
    
    # Employee Management
    path('manage_employees/', views.manage_employees, name='manage_employees'),
    path('add_employee/', views.add_employee, name='add_employee'),
    path('edit_employee/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('delete_employee/<int:employee_id>/', views.delete_employee, name='delete_employee'),
    # ==============================
    #   INVENTORY MANAGEMENT (admin)
    # ==============================
    path("admin_manage-inventory/", views.admin_manage_inventory, name="admin_manage_inventory"),
    path("admin_manage-inventory/approve/<int:product_id>/", views.approve_product, name="approve_product"),
    path("admin_manage-inventory/reject/<int:product_id>/", views.reject_product, name="reject_product"),
    #path("admin_manage-inventory/edit/<int:product_id>/", views.edit_product, name="edit_product"),
    #path("admin_manage-inventory/delete/<int:product_id>/", views.delete_product, name="delete_product"),

    # ==============================
    #   INVENTORY MANAGEMENT (admin)
    # ==============================
    path("employee_inventory/", views.employee_inventory, name="employee_inventory"),
    path("employee_add_product/", views.employee_add_product, name="employee_add_product"),
    path("delete-product/<int:product_id>/", views.delete_product, name="delete_product"),
    path("update-availability/<int:product_id>/", views.update_availability, name="update_availability"),

    # ==============================
    #     PRODUCT LISTING & SEARCH
    # ==============================
    path("products/search/", views.search_products, name="search_products"),
    path("trending_products/", views.trending_products, name="trending_products"),

    # ==============================
    #    RENTAL & PAYMENT PROCESSING
    # ==============================
    path("rent/<int:product_id>/", views.rent_product, name="rent_product"),
    path("booking/confirmation/<int:booking_id>/", views.booking_confirmation, name="booking_confirmation"),
    path("payment_page/", views.payment_page, name="payment_page"),

    # ==============================
    #   FEEDBACK & COMPLAINTS (ADMIN & EMPLOYEE)
    # ==============================
    path("feedback/submit/", views.feedback, name="feedback"),
    path("complaint/submit/", views.complaint, name="complaint"),
    path("resolve_complaints/", views.resolve_complaints, name="resolve_complaints"),  # Admin-only
    
    # ==============================
    #        CHATBOT SUPPORT
    # ==============================
    path("chatbot/support/", views.chatbot_support, name="chatbot_support"),

    # ==============================
    #         REPORTS
    # ==============================
    path("view_reports/", views.view_reports, name="view_reports"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
