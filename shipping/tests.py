from decimal import Decimal
from django.test import TestCase

from shipping.models import ShippingZone
from shipping.services import calculate_shipping_charge
from store_settings.models import SiteConfiguration


class ShippingTests(TestCase):
    def setUp(self):
        self.config = SiteConfiguration.get_solo()
        self.config.free_shipping_threshold = Decimal("2500.00")
        self.config.save()

        self.dhaka_zone = ShippingZone.objects.create(
            code="DHAKA",
            name_en="Inside Dhaka",
            name_bn="ঢাকা মেট্রো",
            charge=Decimal("70.00"),
            free_delivery_allowed=True
        )

        self.outside_zone = ShippingZone.objects.create(
            code="OUTSIDE",
            name_en="Outside Dhaka",
            name_bn="ঢাকার বাইরে",
            charge=Decimal("130.00"),
            free_delivery_allowed=True
        )

    def test_standard_shipping_charge(self):
        # Subtotal ৳ 1500 < ৳ 2500
        charge, zone, is_free = calculate_shipping_charge("DHAKA", Decimal("1500.00"))
        self.assertEqual(charge, Decimal("70.00"))
        self.assertFalse(is_free)

        charge_out, zone_out, is_free_out = calculate_shipping_charge("OUTSIDE", Decimal("1500.00"))
        self.assertEqual(charge_out, Decimal("130.00"))
        self.assertFalse(is_free_out)

    def test_free_shipping_threshold_met(self):
        # Subtotal ৳ 2600 >= ৳ 2500
        charge, zone, is_free = calculate_shipping_charge("DHAKA", Decimal("2600.00"))
        self.assertEqual(charge, Decimal("0.00"))
        self.assertTrue(is_free)
