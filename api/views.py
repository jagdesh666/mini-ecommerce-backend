from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test

from .models import Product, Coupon, Order, OrderItem, Cart, CartItem
from .serializers import ProductSerializer, RegisterSerializer, UserSerializer, OrderSerializer, CartItemSerializer


# ================= USER & AUTH APIs =================

@api_view(['POST'])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({"user": UserSerializer(user).data, "token": token.key}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({"user": UserSerializer(user).data, "token": token.key})
    return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)


# ================= PRODUCT & CART APIs =================

@api_view(['GET'])
def product_list(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def validate_coupon(request):
    code = request.data.get('code')
    cart_value = float(request.data.get('cart_value', 0))

    try:
        coupon = Coupon.objects.get(code=code, active=True)
        now = timezone.now()
        if not (coupon.valid_from <= now <= coupon.valid_to):
            return Response({"error": "Coupon expired"}, status=400)

        if cart_value < coupon.min_cart_value:
            return Response({"error": f"Minimum order should be {coupon.min_cart_value}"}, status=400)

        return Response({
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value
        })
    except Coupon.DoesNotExist:
        return Response({"error": "Invalid Coupon Code"}, status=400)


# ================= ORDER PLACEMENT API =================

@api_view(['POST'])
def place_order(request):
    data = request.data
    # Check if request has a valid token for User, else it's a Guest
    user = request.user if request.user.is_authenticated else None

    full_name = data.get('full_name')
    email = data.get('email')
    cart_items = data.get('items')  # Format: [{"product_id": 1, "quantity": 2}]
    coupon_code = data.get('coupon_code')

    if not cart_items:
        return Response({"error": "Cart is empty"}, status=400)

    total_amount = 0
    order_items_to_prepare = []

    # 1. Stock Validation
    for item in cart_items:
        product = get_object_or_404(Product, id=item['product_id'])
        if product.stock < item['quantity']:
            return Response({"error": f"Not enough stock for {product.name}"}, status=400)

        item_total = float(product.price) * int(item['quantity'])
        total_amount += item_total
        order_items_to_prepare.append({
            'product': product,
            'quantity': item['quantity'],
            'price': product.price
        })

    # 2. Coupon Application
    coupon_obj = None
    if coupon_code:
        try:
            coupon_obj = Coupon.objects.get(code=coupon_code, active=True)
            if total_amount >= coupon_obj.min_cart_value:
                if coupon_obj.discount_type == 'flat':
                    total_amount -= float(coupon_obj.discount_value)
                else:
                    total_amount -= (total_amount * float(coupon_obj.discount_value) / 100)
        except Coupon.DoesNotExist:
            pass

    # 3. Create Order
    order = Order.objects.create(
        user=user,
        full_name=full_name,
        email=email,
        total_amount=max(total_amount, 0),
        coupon_applied=coupon_obj
    )

    # 4. Save Items & Update Stock
    for item in order_items_to_prepare:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
            price=item['price']
        )
        item['product'].stock -= item['quantity']
        item['product'].save()

    return Response({"message": "Order placed successfully", "order_id": order.id}, status=201)


# ================= ADMIN DASHBOARD (Jinja Templates) =================

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'dashboard/index.html', {'orders': orders})


@user_passes_test(lambda u: u.is_staff)
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        order.save()
    return redirect('admin_dashboard')


@user_passes_test(lambda u: u.is_staff)
def manage_products(request):
    products = Product.objects.all()
    if request.method == 'POST':
        Product.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            price=request.POST.get('price'),
            stock=request.POST.get('stock'),
            # Image handling would go here
        )
        return redirect('manage_products')
    return render(request, 'dashboard/products.html', {'products': products})


@user_passes_test(lambda u: u.is_staff)
def manage_coupons(request):
    coupons = Coupon.objects.all()
    if request.method == 'POST':
        Coupon.objects.create(
            code=request.POST.get('code'),
            discount_type=request.POST.get('discount_type'),
            discount_value=request.POST.get('discount_value'),
            min_cart_value=request.POST.get('min_cart_value'),
            valid_from=request.POST.get('valid_from'),
            valid_to=request.POST.get('valid_to'),
        )
        return redirect('manage_coupons')
    return render(request, 'dashboard/coupons.html', {'coupons': coupons})


# ================= CART MANAGEMENT APIs =================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cart_operations(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response({"cart_id": cart.id, "items": serializer.data})

    if request.method == 'POST':
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        return Response({"message": "Added to cart"}, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return Response({"message": "Removed from cart"}, status=204)