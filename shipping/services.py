from decimal import Decimal
from shipping.models import ShippingZone
from store_settings.models import SiteConfiguration


def calculate_shipping_charge(zone_code_or_obj, subtotal):
    """
    Computes shipping charge taking into account:
    - Selected shipping zone
    - Cart subtotal vs. SiteConfiguration.free_shipping_threshold
    - Zone eligibility for free shipping
    Returns tuple: (Decimal shipping_charge, ShippingZone object, bool is_free)
    """
    if isinstance(zone_code_or_obj, ShippingZone):
        zone = zone_code_or_obj
    else:
        zone = ShippingZone.objects.filter(code=str(zone_code_or_obj), is_active=True).first()
        if not zone:
            zone = ShippingZone.get_default_zone()

    site_config = SiteConfiguration.get_solo()
    free_threshold = site_config.free_shipping_threshold
    
    subtotal_decimal = Decimal(str(subtotal))

    if zone.free_delivery_allowed and subtotal_decimal >= free_threshold:
        return Decimal("0.00"), zone, True
    
    return zone.charge, zone, False
