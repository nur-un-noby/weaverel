from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class ShippingZone(models.Model):
    """
    Configurable Bangladesh delivery zones and shipping rates.
    Allows administrators to change fees without altering code.
    """
    code = models.CharField(max_length=50, unique=True, help_text=_("Unique identifier, e.g., DHAKA, SUBURB, OUTSIDE"))
    name_en = models.CharField(max_length=150, help_text=_("Zone name in English (e.g. Inside Dhaka)"))
    name_bn = models.CharField(max_length=150, help_text=_("Zone name in Bangla (e.g. ঢাকা মেট্রো)"))
    charge = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal("70.00"),
        help_text=_("Standard delivery charge in BDT (৳)")
    )
    estimated_delivery_en = models.CharField(max_length=100, default="1-2 business days")
    estimated_delivery_bn = models.CharField(max_length=100, default="১-২ কর্মদিবস")
    free_delivery_allowed = models.BooleanField(
        default=True, 
        help_text=_("Allow free shipping if cart exceeds store threshold")
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = _("Shipping Zone")
        verbose_name_plural = _("Shipping Zones")

    def __str__(self):
        return f"{self.name_en} ({self.name_bn}) - ৳ {int(self.charge)}"

    @classmethod
    def get_default_zone(cls):
        zone = cls.objects.filter(is_active=True).order_by('display_order').first()
        if not zone:
            zone = cls.objects.create(
                code='DHAKA',
                name_en='Inside Dhaka / Dhaka Metro',
                name_bn='ঢাকা মেট্রো',
                charge=Decimal('70.00'),
                estimated_delivery_en='24-48 hours',
                estimated_delivery_bn='২৪-৪৮ ঘণ্টা',
                display_order=1
            )
        return zone
