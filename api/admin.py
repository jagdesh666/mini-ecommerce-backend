from django.contrib import admin
from .models import Product, Coupon, Order, OrderItem, Cart, CartItem

admin.site.register(Product)
admin.site.register(Coupon)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Cart)
admin.site.register(CartItem)