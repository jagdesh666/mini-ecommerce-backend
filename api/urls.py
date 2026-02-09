from django.urls import path
from . import views

urlpatterns = [
    # --- Auth & User APIs ---
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),

    # --- Product & Order APIs ---
    path('products/', views.product_list, name='product-list'),
    path('validate-coupon/', views.validate_coupon, name='validate-coupon'),
    path('place-order/', views.place_order, name='place-order'),

    # --- Custom Admin Dashboard URLs ---
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/status-update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('dashboard/products/', views.manage_products, name='manage_products'),
    path('dashboard/coupons/', views.manage_coupons, name='manage_coupons'),


    # --- Cart APIs ---
    path('cart/', views.cart_operations, name='cart-ops'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='cart-remove'),
]