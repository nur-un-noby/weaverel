from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from promotions.models import Coupon, CouponUsage
from promotions.services import validate_coupon_code


class CouponPromotionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='promocustomer', password='password123')
        
        # 10% coupon, min spend ৳ 1000, max discount ৳ 300
        self.percent_coupon = Coupon.objects.create(
            code="EID2026",
            discount_type=Coupon.DISCOUNT_PERCENTAGE,
            discount_value=Decimal("10.00"),
            min_purchase_amount=Decimal("1000.00"),
            max_discount_amount=Decimal("300.00"),
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            usage_limit=10,
            per_customer_limit=1,
            is_active=True
        )

        # Fixed ৳ 200 coupon
        self.fixed_coupon = Coupon.objects.create(
            code="SAVE200",
            discount_type=Coupon.DISCOUNT_FIXED,
            discount_value=Decimal("200.00"),
            min_purchase_amount=Decimal("1500.00"),
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True
        )

    def test_percentage_coupon_calculation(self):
        # Subtotal ৳ 2000 -> 10% is ৳ 200
        valid, discount, msg, c_obj = validate_coupon_code("EID2026", Decimal("2000.00"), user=self.user)
        self.assertTrue(valid)
        self.assertEqual(discount, Decimal("200.00"))

        # Subtotal ৳ 5000 -> 10% would be ৳ 500, but capped at max ৳ 300
        valid, discount, msg, c_obj = validate_coupon_code("EID2026", Decimal("5000.00"), user=self.user)
        self.assertTrue(valid)
        self.assertEqual(discount, Decimal("300.00"))

    def test_coupon_min_purchase_validation(self):
        # Subtotal ৳ 800 < ৳ 1000 min spend
        valid, discount, msg, c_obj = validate_coupon_code("EID2026", Decimal("800.00"), user=self.user)
        self.assertFalse(valid)
        self.assertEqual(discount, Decimal("0.00"))
        self.assertIn("minimum purchase", msg)

    def test_per_customer_limit(self):
        # Record 1 usage for this customer
        CouponUsage.objects.create(
            coupon=self.percent_coupon,
            user=self.user,
            order_number="WV-TEST-01",
            discount_applied=Decimal("200.00")
        )
        self.percent_coupon.usage_count = 1
        self.percent_coupon.save()

        # Try to use again
        valid, discount, msg, c_obj = validate_coupon_code("EID2026", Decimal("2000.00"), user=self.user)
        self.assertFalse(valid)
        self.assertIn("already used this coupon", msg)
