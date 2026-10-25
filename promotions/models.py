from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Coupon(models.Model):
    DISCOUNT_PERCENTAGE = 'PERCENT'
    DISCOUNT_FIXED = 'FIXED'
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_PERCENTAGE, _('Percentage Discount (%)')),
        (DISCOUNT_FIXED, _('Fixed Amount Discount (৳)')),
    ]

    code = models.CharField(max_length=50, unique=True, help_text=_("Coupon Code (e.g., EID2026, SAVE10)"))
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default=DISCOUNT_PERCENTAGE)
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text=_("Percentage (e.g. 10 for 10%) or Fixed BDT (e.g. 200 for ৳ 200)")
    )
    min_purchase_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal("0.00"),
        help_text=_("Minimum order subtotal in BDT to qualify")
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text=_("Maximum discount cap in BDT for percentage discounts")
    )
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text=_("Total global usage limit (blank for unlimited)"))
    usage_count = models.PositiveIntegerField(default=0)
    per_customer_limit = models.PositiveIntegerField(default=1, help_text=_("Times an individual customer can use this"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")

    def __str__(self):
        val = f"{int(self.discount_value)}%" if self.discount_type == self.DISCOUNT_PERCENTAGE else f"৳ {int(self.discount_value)}"
        return f"{self.code} ({val} off)"

    def is_valid_now(self):
        now = timezone.now()
        if not self.is_active:
            return False, _("This coupon is inactive.")
        if self.valid_from and now < self.valid_from:
            return False, _("This coupon has not started yet.")
        if self.valid_to and now > self.valid_to:
            return False, _("This coupon has expired.")
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return False, _("This coupon has reached its maximum global usage limit.")
        return True, ""

    def calculate_discount(self, subtotal):
        subtotal_dec = Decimal(str(subtotal))
        if subtotal_dec < self.min_purchase_amount:
            return Decimal("0.00")
        
        if self.discount_type == self.DISCOUNT_PERCENTAGE:
            discount = (subtotal_dec * self.discount_value) / Decimal("100.00")
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
        else:
            discount = self.discount_value

        # Cannot exceed subtotal
        if discount > subtotal_dec:
            discount = subtotal_dec

        return round(discount, 2)


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='coupon_usages')
    guest_phone = models.CharField(max_length=30, blank=True)
    order_number = models.CharField(max_length=50)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']
        verbose_name = _("Coupon Usage")
        verbose_name_plural = _("Coupon Usages")

    def __str__(self):
        return f"{self.coupon.code} used on {self.order_number}"
