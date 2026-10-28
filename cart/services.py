from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Cart, CartItem
from store.models import Product, ProductVariant
from shipping.models import ShippingZone
from shipping.services import calculate_shipping_charge
from shipping.districts import normalize_district
from promotions.models import Coupon, CouponUsage
from promotions.services import validate_coupon_code
from store_settings.models import SiteConfiguration
from orders.models import Order, OrderItem
from accounts.models import validate_bangladesh_phone


def get_or_create_cart(request):
    """
    Returns the active database Cart for the current request.
    Handles both authenticated users and anonymous visitors with persistent sessions.
    """
    if getattr(request, 'user', None) and request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session = getattr(request, 'session', None)
        if session is not None and not session.session_key:
            session.create()
        session_key = session.session_key if session else None
        if hasattr(request, 'cart') and request.cart:
            return request.cart
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


def merge_guest_cart_into_user_cart(request, user, guest_session_key=None):
    """
    Called upon user login:
    Transfers any items from the guest session cart into the user's permanent cart.
    """
    session_key = guest_session_key or (request.session.session_key if hasattr(request, 'session') else None)
    if not session_key:
        return

    guest_cart = Cart.objects.filter(session_key=session_key).first()
    if not guest_cart or not guest_cart.items.exists():
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for g_item in guest_cart.items.all():
        u_item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            variant=g_item.variant,
            defaults={'quantity': g_item.quantity}
        )
        if not created:
            u_item.quantity += g_item.quantity
            u_item.save(update_fields=['quantity', 'updated_at'])

    guest_cart.items.all().delete()
    guest_cart.delete()


def add_item_to_cart(cart, variant_id, quantity=1):
    """
    Adds a product variant to cart with server-side stock validation.
    Returns: (bool success, str message, CartItem item)
    """
    variant = ProductVariant.objects.filter(id=variant_id, is_active=True).select_related('product').first()
    if not variant:
        return False, _("Selected clothing variant is unavailable."), None

    if variant.stock < 1:
        return False, _(f"Sorry, '{variant.product.name}' is currently out of stock."), None

    try:
        qty = max(1, int(quantity))
    except (ValueError, TypeError):
        qty = 1

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={'quantity': qty}
    )

    if not created:
        new_quantity = cart_item.quantity + qty
        if new_quantity > variant.stock:
            return False, _(f"Only {variant.stock} items available in stock."), cart_item
        cart_item.quantity = new_quantity
        cart_item.save(update_fields=['quantity', 'updated_at'])
    else:
        if cart_item.quantity > variant.stock:
            cart_item.quantity = variant.stock
            cart_item.save(update_fields=['quantity', 'updated_at'])

    return True, _(f"Added {variant.product.name} ({variant.size.name if variant.size else 'Standard'}) to your cart!"), cart_item


def calculate_order_financials(cart, zone_code=None, coupon_code=None, user=None, phone=None):
    """
    Recalculates prices, discounts, and totals on the server.
    Never trusts client-submitted financial values.
    """
    subtotal = Decimal('0.00')
    cart_items = list(cart.items.select_related('variant', 'variant__product', 'variant__size', 'variant__color'))
    for item in cart_items:
        subtotal += item.variant.current_price * item.quantity

    # 1. Shipping
    shipping_charge, zone, is_free_shipping = calculate_shipping_charge(zone_code or 'DHAKA', subtotal)

    # 2. Coupon Discount
    discount_amount = Decimal('0.00')
    coupon_obj = None
    coupon_msg = ""
    if coupon_code:
        valid, disc, msg, c_obj = validate_coupon_code(coupon_code, subtotal, user=user, phone=phone)
        if valid:
            discount_amount = disc
            coupon_obj = c_obj
            coupon_msg = msg
        else:
            coupon_msg = msg

    # Final Total (guaranteed non-negative)
    total_amount = max(Decimal('0.00'), subtotal - discount_amount + shipping_charge)

    return {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'subtotal_formatted': f"৳ {int(subtotal):,}",
        'shipping_charge': shipping_charge,
        'shipping_charge_formatted': f"৳ {int(shipping_charge):,}" if shipping_charge > 0 else "বিনামূল্যে (Free)",
        'zone': zone,
        'is_free_shipping': is_free_shipping,
        'discount_amount': discount_amount,
        'discount_amount_formatted': f"৳ {int(discount_amount):,}",
        'coupon': coupon_obj,
        'coupon_message': coupon_msg,
        'total_amount': total_amount,
        'total_amount_formatted': f"৳ {int(total_amount):,}",
    }


@transaction.atomic
def process_checkout(request, form_data):
    """
    Processes the entire checkout atomically:
    1. Revalidates cart items
    2. Locks variant inventory rows (select_for_update) to prevent overselling
    3. Verifies stock availability
    4. Computes server-authoritative totals
    5. Deducts inventory safely
    6. Creates Order & OrderItem snapshot records
    7. Tracks coupon usage if applied
    8. Clears the cart
    """
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        raise ValidationError(_("Your shopping cart is empty."))

    user = request.user if (getattr(request, 'user', None) and request.user.is_authenticated) else None

    phone = form_data.get('phone_number', '').strip()
    full_name = form_data.get('full_name', '').strip()
    address = form_data.get('address', '').strip()
    delivery_zone_code = form_data.get('delivery_zone', 'DHAKA')
    payment_method = form_data.get('payment_method', Order.PAYMENT_COD)
    customer_notes = form_data.get('customer_notes', '').strip()
    coupon_code = form_data.get('coupon_code', '').strip()
    email = form_data.get('email', '').strip()

    if not full_name or not phone or not address:
        raise ValidationError(_("আপনার পুরো নাম, মোবাইল নম্বর এবং সম্পূর্ণ ডেলিভারি ঠিকানা দিন। (Full Name, Phone, and Address are required)"))

    is_valid_phone, clean_phone = validate_bangladesh_phone(phone)
    if not is_valid_phone:
        raise ValidationError(_("সঠিক ১১ ডিজিটের বাংলাদেশি মোবাইল নম্বর দিন (যেমন: 017XXXXXXXX বা ০১৭১২৩৪৫৬৭৮)"))

    phone = clean_phone

    # Clean alternative phone if provided
    alt_phone = form_data.get('alternative_phone', '').strip()
    if alt_phone:
        is_alt_valid, clean_alt = validate_bangladesh_phone(alt_phone)
        if is_alt_valid:
            alt_phone = clean_alt

    # If unauthenticated, associate with existing customer profile if matched by phone
    if not user:
        from accounts.models import CustomerProfile
        matched_profile = CustomerProfile.objects.filter(phone_number=phone).select_related('user').first()
        if matched_profile and matched_profile.user:
            user = matched_profile.user

    # If user is logged in, sync phone and address to profile if currently empty
    if user and hasattr(user, 'profile'):
        profile_updated = False
        if not user.profile.phone_number:
            user.profile.phone_number = phone
            profile_updated = True
        if not user.profile.address and address:
            user.profile.address = address
            user.profile.district = normalize_district(form_data.get('district', 'Dhaka'))
            profile_updated = True
        if profile_updated:
            user.profile.save()

    # 1. Lock and validate inventory concurrently
    item_ids = list(cart.items.values_list('id', flat=True))
    items_locked = CartItem.objects.filter(id__in=item_ids).select_related('variant', 'variant__product').select_for_update()

    for item in items_locked:
        variant = item.variant
        if not variant.is_active or variant.stock < item.quantity:
            raise ValidationError(
                _(f"Insufficient stock for '{variant.product.name} ({variant.size.name if variant.size else ''})'. Only {variant.stock} left in stock.")
            )

    # 2. Recalculate authoritative totals
    financials = calculate_order_financials(
        cart=cart,
        zone_code=delivery_zone_code,
        coupon_code=coupon_code,
        user=user,
        phone=phone
    )

    # 3. Create Order
    order = Order.objects.create(
        user=user,
        full_name=full_name,
        phone_number=phone,
        alternative_phone=alt_phone,
        email=email,
        delivery_zone=delivery_zone_code,
        shipping_zone=financials['zone'],
        district=normalize_district(form_data.get('district', 'Dhaka')),
        address=address,
        payment_method=payment_method,
        payment_status=Order.PAYMENT_STATUS_PENDING,
        status=Order.STATUS_PENDING,
        subtotal=financials['subtotal'],
        discount_amount=financials['discount_amount'],
        delivery_charge=financials['shipping_charge'],
        total_amount=financials['total_amount'],
        coupon=financials['coupon'],
        coupon_code=financials['coupon'].code if financials['coupon'] else '',
        customer_notes=customer_notes,
    )

    # 4. Create OrderItems snapshot and decrement inventory
    for item in items_locked:
        variant = item.variant
        variant.stock -= item.quantity
        variant.save(update_fields=['stock', 'updated_at'])

        OrderItem.objects.create(
            order=order,
            product=variant.product,
            variant=variant,
            product_name=variant.product.name,
            product_name_bn=variant.product.name_bn,
            product_sku=variant.sku,
            size=variant.size.name if variant.size else 'Standard',
            color_name=variant.color.name if variant.color else '',
            price=variant.current_price,
            quantity=item.quantity,
            total_price=variant.current_price * item.quantity,
        )

    # 5. Record coupon usage
    if financials['coupon']:
        CouponUsage.objects.create(
            coupon=financials['coupon'],
            user=user,
            guest_phone=phone,
            order_number=order.order_number,
            discount_applied=financials['discount_amount'],
        )
        financials['coupon'].usage_count += 1
        financials['coupon'].save(update_fields=['usage_count'])

    # 6. Clear shopping cart
    cart.clear()

    return order
