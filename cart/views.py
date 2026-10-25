from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from store.models import Product
from orders.models import Order, OrderItem


def cart_detail(request):
    """
    Shopping bag page with BDT calculations and delivery estimation.
    """
    cart = request.session.get('cart', {})
    cart_items = list(cart.values())

    subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)
    
    # Free delivery on orders over ৳ 2,500
    free_delivery_threshold = 2500.0
    qualifies_for_free_delivery = subtotal >= free_delivery_threshold
    amount_needed_for_free_delivery = max(0, free_delivery_threshold - subtotal)
    
    # Standard initial delivery charge estimate (Inside Dhaka ৳ 70)
    estimated_delivery = 0.0 if qualifies_for_free_delivery else 70.0
    estimated_total = subtotal + estimated_delivery

    context = {
        'cart_items': cart_items,
        'subtotal': round(subtotal, 2),
        'subtotal_bdt': f"৳ {int(subtotal):,}",
        'free_delivery_threshold': free_delivery_threshold,
        'qualifies_for_free_delivery': qualifies_for_free_delivery,
        'amount_needed_for_free_delivery': round(amount_needed_for_free_delivery, 2),
        'amount_needed_bdt': f"৳ {int(amount_needed_for_free_delivery):,}",
        'estimated_delivery': int(estimated_delivery),
        'estimated_total_bdt': f"৳ {int(estimated_total):,}",
    }
    return render(request, 'cart/cart_detail.html', context)


def add_to_cart(request, product_id):
    """
    Adds a clothing product (with chosen size and quantity) to session cart.
    """
    product = get_object_or_404(Product, id=product_id, is_available=True)
    size = request.POST.get('size') or request.GET.get('size') or (product.size_list[0] if product.size_list else 'Standard')
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    cart = request.session.get('cart', {})
    item_key = f"{product.id}_{size}"

    if item_key in cart:
        cart[item_key]['quantity'] += quantity
    else:
        cart[item_key] = {
            'key': item_key,
            'product_id': product.id,
            'sku': product.sku,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.current_price),
            'original_price': float(product.price),
            'formatted_price': f"৳ {int(product.current_price):,}",
            'size': size,
            'quantity': quantity,
            'image': product.display_image,
        }

    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f'"{product.name}" (সাইজ: {size}) ব্যাগে যুক্ত হয়েছে!')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'cart:cart_detail'
    return redirect(next_url)


def update_cart(request, item_key):
    """
    Adjusts quantity (+ / -) in the shopping bag.
    """
    cart = request.session.get('cart', {})
    action = request.POST.get('action') or request.GET.get('action')

    if item_key in cart:
        if action == 'increase':
            cart[item_key]['quantity'] += 1
        elif action == 'decrease':
            cart[item_key]['quantity'] -= 1
            if cart[item_key]['quantity'] <= 0:
                del cart[item_key]
        request.session['cart'] = cart
        request.session.modified = True

    return redirect('cart:cart_detail')


def remove_from_cart(request, item_key):
    """
    Removes an item completely from the bag.
    """
    cart = request.session.get('cart', {})
    if item_key in cart:
        removed_name = cart[item_key]['name']
        del cart[item_key]
        request.session['cart'] = cart
        request.session.modified = True
        messages.info(request, f'"{removed_name}" ব্যাগ থেকে সরানো হয়েছে।')

    return redirect('cart:cart_detail')


def checkout_view(request):
    """
    Enterprise checkout view with Cash on Delivery and bKash options.
    Creates a real database Order and OrderItem records.
    """
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "আপনার ব্যাগ খালি! অর্ডার করতে পণ্য যুক্ত করুন। (Your bag is empty)")
        return redirect('store:home')

    cart_items = list(cart.values())
    subtotal = sum(float(item['price']) * item['quantity'] for item in cart_items)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        alternative_phone = request.POST.get('alternative_phone', '').strip()
        address = request.POST.get('address', '').strip()
        delivery_zone = request.POST.get('delivery_zone', 'DHAKA')
        payment_method = request.POST.get('payment_method', 'COD')
        customer_notes = request.POST.get('customer_notes', '').strip()

        # Simple validation for mass audience
        if not full_name or not phone_number or not address:
            messages.error(request, "দয়া করে আপনার নাম, মোবাইল নম্বর এবং সম্পূর্ণ ঠিকানা সঠিকভাবে লিখুন।")
            return redirect('cart:checkout')

        # Determine delivery fee
        if subtotal >= 2500.0:
            delivery_charge = 0.0
        elif delivery_zone == 'OUTSIDE':
            delivery_charge = 130.0
        elif delivery_zone == 'SUBURB':
            delivery_charge = 100.0
        else:
            delivery_charge = 70.0

        total_amount = subtotal + delivery_charge

        # 1. Create real Order
        order = Order.objects.create(
            full_name=full_name,
            phone_number=phone_number,
            alternative_phone=alternative_phone,
            address=address,
            delivery_zone=delivery_zone,
            payment_method=payment_method,
            subtotal=subtotal,
            delivery_charge=delivery_charge,
            total_amount=total_amount,
            customer_notes=customer_notes,
            status='PENDING'
        )

        # 2. Create OrderItems and adjust inventory
        for item in cart_items:
            product = Product.objects.filter(id=item.get('product_id')).first()
            if product and product.stock >= item['quantity']:
                product.stock -= item['quantity']
                product.save()

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=item['name'],
                product_sku=item.get('sku', ''),
                size=item.get('size', 'Standard'),
                price=item['price'],
                quantity=item['quantity'],
                total_price=float(item['price']) * item['quantity']
            )

        # 3. Clear shopping bag session
        request.session['cart'] = {}
        request.session.modified = True

        messages.success(request, f"ধন্যবাদ! আপনার অর্ডার #{order.order_number} সফলভাবে গৃহীত হয়েছে।")
        return redirect('cart:order_success', order_number=order.order_number)

    # GET request: render checkout form
    context = {
        'cart_items': cart_items,
        'subtotal': round(subtotal, 2),
        'subtotal_bdt': f"৳ {int(subtotal):,}",
        'free_delivery': subtotal >= 2500.0,
    }
    return render(request, 'cart/checkout.html', context)


def order_success_view(request, order_number):
    """
    Displays the confirmed order invoice with tracking details.
    """
    order = get_object_or_404(Order, order_number=order_number)
    context = {
        'order': order,
        'items': order.items.all(),
        'subtotal_bdt': f"৳ {int(order.subtotal):,}",
        'delivery_charge_bdt': f"৳ {int(order.delivery_charge):,}" if order.delivery_charge > 0 else "বিনামূল্যে (Free)",
        'total_amount_bdt': f"৳ {int(order.total_amount):,}",
    }
    return render(request, 'cart/order_success.html', context)
