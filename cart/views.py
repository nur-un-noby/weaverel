from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_GET
from django.utils.translation import gettext_lazy as _

from .models import Cart, CartItem
from .services import (
    get_or_create_cart,
    add_item_to_cart,
    calculate_order_financials,
    process_checkout,
)
from store.models import Product, ProductVariant
from orders.models import Order
from shipping.models import ShippingZone
from store_settings.models import SiteConfiguration


def cart_detail(request):
    """
    Shopping bag full page view with BDT calculations,
    free shipping progress meter, and checkout link.
    """
    cart = get_or_create_cart(request)
    financials = calculate_order_financials(cart)
    
    config = SiteConfiguration.get_solo()
    free_threshold = config.free_shipping_threshold
    subtotal = financials['subtotal']
    
    needed_for_free = max(0, free_threshold - subtotal)
    progress_pct = min(100, int((subtotal / free_threshold) * 100)) if free_threshold > 0 else 100

    context = {
        'cart': cart,
        'cart_items': financials['cart_items'],
        'subtotal': subtotal,
        'subtotal_formatted': financials['subtotal_formatted'],
        'estimated_shipping': financials['shipping_charge'],
        'estimated_shipping_formatted': financials['shipping_charge_formatted'],
        'total_amount': financials['total_amount'],
        'total_amount_formatted': financials['total_amount_formatted'],
        'free_threshold': free_threshold,
        'is_free_shipping': financials['is_free_shipping'],
        'needed_for_free': needed_for_free,
        'needed_for_free_formatted': f"৳ {int(needed_for_free):,}",
        'progress_pct': progress_pct,
    }
    return render(request, 'cart/cart_detail.html', context)


def cart_drawer(request):
    """
    HTMX slide-over cart drawer partial for instant seamless shopping bag previews.
    """
    cart = get_or_create_cart(request)
    financials = calculate_order_financials(cart)
    
    config = SiteConfiguration.get_solo()
    needed_for_free = max(0, config.free_shipping_threshold - financials['subtotal'])

    context = {
        'cart': cart,
        'cart_items': financials['cart_items'],
        'subtotal': financials['subtotal'],
        'subtotal_formatted': financials['subtotal_formatted'],
        'total_amount_formatted': financials['total_amount_formatted'],
        'free_threshold': config.free_shipping_threshold,
        'is_free_shipping': financials['is_free_shipping'],
        'needed_for_free_formatted': f"৳ {int(needed_for_free):,}",
    }
    return render(request, 'cart/partials/cart_drawer.html', context)


def add_to_cart(request, product_id):
    """
    Adds a clothing product or specific variant to the shopping bag.
    Supports both standard form submission and HTMX drawer trigger.
    """
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id, is_available=True)
    
    variant_id = request.POST.get('variant_id') or request.GET.get('variant_id')
    quantity = request.POST.get('quantity', 1)

    variant = None
    if variant_id:
        variant = ProductVariant.objects.filter(id=variant_id, product=product, is_active=True).first()

    if not variant:
        # Check size and color posted
        size_name = request.POST.get('size')
        color_name = request.POST.get('color')
        query = ProductVariant.objects.filter(product=product, is_active=True)
        if size_name:
            query = query.filter(size__name=size_name)
        if color_name:
            query = query.filter(color__name=color_name)
        variant = query.first()

    if not variant:
        # Fallback to first active variant in stock
        variant = product.variants.filter(is_active=True, stock__gt=0).first() or product.variants.filter(is_active=True).first()

    if not variant:
        messages.error(request, _("This product has no active variants in stock."))
        return redirect('store:product_detail', slug=product.slug)

    success, msg, cart_item = add_item_to_cart(cart, variant.id, quantity)

    if success:
        messages.success(request, msg)
    else:
        messages.warning(request, msg)

    if request.headers.get('HX-Request'):
        return cart_drawer(request)

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'cart:cart_detail'
    return redirect(next_url)


def update_cart(request, item_id):
    """
    Adjusts item quantity (+ / -) in the shopping bag.
    """
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    action = request.POST.get('action') or request.GET.get('action')

    if action == 'increase':
        if item.quantity < item.variant.stock:
            item.quantity += 1
            item.save(update_fields=['quantity', 'updated_at'])
        else:
            messages.warning(request, f"সর্বোচ্চ {item.variant.stock} টি উপলব্ধ আছে (Max stock reached)")
    elif action == 'decrease':
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
        else:
            item.save(update_fields=['quantity', 'updated_at'])

    if request.headers.get('HX-Request'):
        if request.GET.get('view') == 'page':
            return cart_detail(request)
        return cart_drawer(request)

    return redirect('cart:cart_detail')


def remove_from_cart(request, item_id):
    """
    Completely removes a line item from the shopping bag.
    """
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    name = f"{item.variant.product.name} ({item.variant.size.name if item.variant.size else ''})"
    item.delete()
    messages.info(request, f'"{name}" কার্ট থেকে সরানো হয়েছে।')

    if request.headers.get('HX-Request'):
        if request.GET.get('view') == 'page':
            return cart_detail(request)
        return cart_drawer(request)

    return redirect('cart:cart_detail')


@require_POST
def apply_coupon(request):
    """
    HTMX / JSON endpoint to preview and apply coupon discount on checkout.
    """
    cart = get_or_create_cart(request)
    code = request.POST.get('coupon_code', '').strip()
    zone_code = request.POST.get('delivery_zone', 'DHAKA')
    user = request.user if request.user.is_authenticated else None
    phone = request.POST.get('phone_number', '')

    financials = calculate_order_financials(
        cart=cart,
        zone_code=zone_code,
        coupon_code=code,
        user=user,
        phone=phone
    )

    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/checkout_summary.html', {'financials': financials})

    return JsonResponse({
        'valid': bool(financials['coupon']),
        'discount_amount': str(financials['discount_amount']),
        'total_amount': str(financials['total_amount']),
        'message': financials['coupon_message'],
    })


def checkout_view(request):
    """
    Mobile-first checkout flow with:
    - Customer details (name, phone, alternative phone, address, district)
    - Delivery zone selection with dynamic rate recalculation
    - Cash on Delivery (ক্যাশ অন ডেলিভারি)
    - Coupon application
    - Safe concurrency inventory locking
    - Seamless checkout for both guest users (using valid phone number) and registered customers
    """
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, "আপনার কার্ট খালি! অর্ডার করতে পণ্য যুক্ত করুন। (Your shopping cart is empty)")
        return redirect('store:home')

    is_customer_authenticated = bool(request.user.is_authenticated)

    if request.method == 'POST':
        try:
            order = process_checkout(request, request.POST)
            messages.success(request, f"ধন্যবাদ! আপনার অর্ডার #{order.order_number} সফলভাবে গৃহীত হয়েছে।")
            return redirect('cart:order_success', order_number=order.order_number)

        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
            return redirect('cart:checkout')

    shipping_zones = ShippingZone.objects.filter(is_active=True).order_by('display_order')

    # Defaults from authenticated customer profile
    default_name = ""
    default_phone = ""
    default_address = ""
    default_district = "Dhaka"
    saved_addresses = []

    if is_customer_authenticated:
        default_name = request.user.get_full_name() or request.user.username
        if hasattr(request.user, 'profile'):
            default_phone = request.user.profile.phone_number
            default_address = request.user.profile.address
            default_district = request.user.profile.district
            saved_addresses = request.user.profile.saved_addresses.all()

    initial_zone = shipping_zones.first().code if shipping_zones.exists() else 'DHAKA'
    financials = calculate_order_financials(cart, zone_code=initial_zone)

    context = {
        'cart': cart,
        'cart_items': financials['cart_items'],
        'financials': financials,
        'shipping_zones': shipping_zones,
        'default_name': default_name,
        'default_phone': default_phone,
        'default_address': default_address,
        'default_district': default_district,
        'saved_addresses': saved_addresses,
        'is_customer_authenticated': is_customer_authenticated,
    }
    return render(request, 'cart/checkout.html', context)


def order_success_view(request, order_number):
    """
    Displays the confirmed order invoice with full details,
    printable packing slip button, and delivery tracking.
    """
    order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_number)
    context = {
        'order': order,
        'items': order.items.all(),
        'subtotal_formatted': f"৳ {int(order.subtotal):,}",
        'discount_formatted': f"৳ {int(order.discount_amount):,}",
        'shipping_charge_formatted': f"৳ {int(order.delivery_charge):,}" if order.delivery_charge > 0 else "বিনামূল্যে (Free)",
        'total_amount_formatted': f"৳ {int(order.total_amount):,}",
    }
    return render(request, 'cart/order_success.html', context)
