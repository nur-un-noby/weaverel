from decimal import Decimal
from promotions.models import Coupon, CouponUsage
from django.utils.translation import gettext_lazy as _


def validate_coupon_code(code_str, subtotal, user=None, phone=None):
    """
    Validates a coupon code server-side against:
    - Existence & active status
    - Date validity (valid_from / valid_to)
    - Global usage limit
    - Minimum purchase amount requirement
    - Per-customer usage limit (by authenticated user or guest phone)
    
    Returns:
    (bool is_valid, Decimal discount_amount, str message, Coupon coupon_obj)
    """
    if not code_str:
        return False, Decimal("0.00"), _("No coupon code provided."), None

    code_clean = code_str.strip().upper()
    coupon = Coupon.objects.filter(code__iexact=code_clean).first()
    if not coupon:
        return False, Decimal("0.00"), _("Invalid coupon code."), None

    valid, err_msg = coupon.is_valid_now()
    if not valid:
        return False, Decimal("0.00"), err_msg, coupon

    subtotal_dec = Decimal(str(subtotal))
    if subtotal_dec < coupon.min_purchase_amount:
        msg = f"This coupon requires a minimum purchase of ৳ {int(coupon.min_purchase_amount):,}."
        return False, Decimal("0.00"), msg, coupon

    # Check per-customer usage limit
    if user and user.is_authenticated:
        user_usages = CouponUsage.objects.filter(coupon=coupon, user=user).count()
        if user_usages >= coupon.per_customer_limit:
            return False, Decimal("0.00"), _("You have already used this coupon maximum allowed times."), coupon
    elif phone:
        phone_clean = phone.strip()
        if phone_clean:
            phone_usages = CouponUsage.objects.filter(coupon=coupon, guest_phone=phone_clean).count()
            if phone_usages >= coupon.per_customer_limit:
                return False, Decimal("0.00"), _("This phone number has already used this coupon."), coupon

    discount = coupon.calculate_discount(subtotal_dec)
    return True, discount, _("Coupon applied successfully!"), coupon
