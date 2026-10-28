from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from store.models import Category, Product, ProductVariant, Size, Color
from cart.models import Cart
from cart.services import add_item_to_cart, process_checkout
from shipping.models import ShippingZone
from promotions.models import Coupon
from orders.models import Order


class UserJourneyAndConcurrencyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Panjabi", slug="panjabi")
        self.size = Size.objects.create(name="42")
        self.color = Color.objects.create(name="White", hex_code="#ffffff")

        self.product = Product.objects.create(
            category=self.category,
            name="Eid Special White Panjabi",
            slug="eid-special-white-panjabi",
            sku="WV-EID-01",
            price=Decimal("2000.00"),
            discount_price=Decimal("1800.00"),
            is_available=True
        )

        # Variant with limited stock of exactly 1 unit
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size=self.size,
            color=self.color,
            sku="WV-EID-01-42-WHT",
            stock=1,
            is_active=True
        )

        self.zone = ShippingZone.objects.create(
            code="DHAKA",
            name_en="Inside Dhaka",
            name_bn="ঢাকা মেট্রো",
            charge=Decimal("70.00"),
            free_delivery_allowed=True
        )

        self.coupon = Coupon.objects.create(
            code="EID2026",
            discount_type=Coupon.DISCOUNT_PERCENTAGE,
            discount_value=Decimal("10.00"),
            min_purchase_amount=Decimal("1000.00"),
            is_active=True
        )

    def test_complete_customer_checkout_journey(self):
        # 1. Browse Homepage
        resp_home = self.client.get(reverse('store:home'))
        self.assertEqual(resp_home.status_code, 200)

        # 2. View Product Details
        resp_prod = self.client.get(reverse('store:product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(resp_prod.status_code, 200)
        self.assertContains(resp_prod, "Eid Special White Panjabi")

        # 3. Add to Cart via POST
        add_url = reverse('cart:add_to_cart', kwargs={'product_id': self.product.id})
        resp_add = self.client.post(add_url, {
            'variant_id': self.variant.id,
            'quantity': 1
        })
        self.assertEqual(resp_add.status_code, 302)

        # 4. View Cart Page
        resp_cart = self.client.get(reverse('cart:cart_detail'))
        self.assertEqual(resp_cart.status_code, 200)
        self.assertContains(resp_cart, "Eid Special White Panjabi")

        # 5. Apply Coupon
        coupon_url = reverse('cart:apply_coupon')
        resp_coupon = self.client.post(coupon_url, {
            'coupon_code': 'EID2026',
            'delivery_zone': 'DHAKA'
        })
        self.assertEqual(resp_coupon.status_code, 200)

        # 5.5 Verify unauthenticated client can access checkout directly
        resp_unauth = self.client.get(reverse('cart:checkout'))
        self.assertEqual(resp_unauth.status_code, 200)

        # 5.6 Automatic Gmail Login
        resp_login = self.client.post(reverse('accounts:google_auto_login'), {
            'email': 'noby@gmail.com',
            'full_name': 'Nurun Noby'
        })
        self.assertEqual(resp_login.status_code, 302)
        self.assertEqual(resp_login.url, reverse('cart:checkout'))

        # 6. Submit Checkout as Authenticated Customer
        checkout_url = reverse('cart:checkout')
        resp_checkout = self.client.post(checkout_url, {
            'full_name': 'Nurun Noby',
            'phone_number': '01712345678',
            'delivery_zone': 'DHAKA',
            'district': 'Dhaka',
            'address': 'House 10, Road 5, Dhanmondi',
            'payment_method': 'COD',
            'coupon_code': 'EID2026',
        })
        self.assertEqual(resp_checkout.status_code, 302)

        order = Order.objects.filter(phone_number='01712345678').first()
        self.assertIsNotNone(order)
        # Expected price: subtotal 1800 - 10% coupon (180) + delivery 70 = 1690
        self.assertEqual(order.subtotal, Decimal("1800.00"))
        self.assertEqual(order.discount_amount, Decimal("180.00"))
        self.assertEqual(order.total_amount, Decimal("1690.00"))
        self.assertEqual(order.status, Order.STATUS_PENDING)

        # Stock should now be 0
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 0)

        # 7. Customer Track Order
        track_url = reverse('store:track_order')
        resp_track = self.client.get(track_url, {'q': order.order_number})
        self.assertEqual(resp_track.status_code, 200)
        self.assertContains(resp_track, order.order_number)

    def test_concurrency_stock_safety_prevents_overselling(self):
        # Variant stock is 1.
        user_a = User.objects.create_user(username='customer_a')
        user_b = User.objects.create_user(username='customer_b')

        # Customer A cart has 1 unit
        cart_a = Cart.objects.create(user=user_a)
        add_item_to_cart(cart_a, self.variant.id, 1)

        # Customer B cart also has 1 unit
        cart_b = Cart.objects.create(user=user_b)
        add_item_to_cart(cart_b, self.variant.id, 1)

        class MockRequest:
            def __init__(self, c, u):
                self.user = u
                self.session = Client().session
                self.cart = c

        req_a = MockRequest(cart_a, user_a)
        req_b = MockRequest(cart_b, user_b)

        # Customer A checks out successfully
        form_data_a = {
            'full_name': 'Customer A',
            'phone_number': '01700000001',
            'address': 'Dhaka',
            'delivery_zone': 'DHAKA',
        }
        order_a = process_checkout(req_a, form_data_a)
        self.assertIsNotNone(order_a)

        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 0)

        # Customer B attempts to checkout with the same variant which is now 0 stock
        form_data_b = {
            'full_name': 'Customer B',
            'phone_number': '01700000002',
            'address': 'Chittagong',
            'delivery_zone': 'OUTSIDE',
        }
        with self.assertRaises(ValidationError) as ctx:
            process_checkout(req_b, form_data_b)

        self.assertIn("Insufficient stock", str(ctx.exception))
        # Ensure only 1 order exists
        self.assertEqual(Order.objects.count(), 1)

    def test_staff_and_guest_can_place_order_with_valid_phone(self):
        """Staff/superuser accounts as well as guest clients can access checkout and place orders with valid phone numbers."""
        staff_user = User.objects.create_user(username='staff_admin', password='pass', is_staff=True, is_superuser=True)
        staff_cart = Cart.objects.create(user=staff_user)
        add_item_to_cart(staff_cart, self.variant.id, 1)

        self.client.login(username='staff_admin', password='pass')

        # GET /cart/checkout/ should succeed (200)
        resp_get = self.client.get(reverse('cart:checkout'))
        self.assertEqual(resp_get.status_code, 200)

        # POST /cart/checkout/ with valid phone should place order successfully
        resp_post = self.client.post(reverse('cart:checkout'), {
            'full_name': 'Admin Person',
            'phone_number': '01711111111',
            'address': 'Dhanmondi, Dhaka',
            'district': 'Dhaka',
            'delivery_zone': 'DHAKA',
            'payment_method': 'COD',
        })
        self.assertEqual(resp_post.status_code, 302)
        admin_order = Order.objects.filter(phone_number='01711111111').first()
        self.assertIsNotNone(admin_order)

    def test_guest_checkout_with_bengali_phone_digits(self):
        """Guest users entering Bengali numeral phone numbers can proceed with order."""
        # Restock variant
        self.variant.stock = 5
        self.variant.save()

        session = self.client.session
        session.create()
        guest_cart = Cart.objects.create(session_key=session.session_key)
        add_item_to_cart(guest_cart, self.variant.id, 1)

        class MockReq:
            def __init__(self, c):
                self.cart = c
                self.user = None
                self.session = Client().session

        form_data = {
            'full_name': 'রহিম উদ্দিন',
            'phone_number': '০১৭১২-৩৪৫৬৭৮',  # Bengali numerals with dash
            'address': 'মিরপুর ১০, ঢাকা',
            'district': 'Dhaka',
            'delivery_zone': 'DHAKA',
            'payment_method': 'COD',
        }
        order = process_checkout(MockReq(guest_cart), form_data)
        self.assertIsNotNone(order)
        self.assertEqual(order.phone_number, '01712345678')
        self.assertEqual(order.full_name, 'রহিম উদ্দিন')

    def test_invalid_phone_number_rejected_during_checkout(self):
        """Invalid phone numbers like 'ghdfsh' or short numbers must be rejected."""
        customer = User.objects.create_user(username='real_customer', email='customer@gmail.com')
        cart = Cart.objects.create(user=customer)
        add_item_to_cart(cart, self.variant.id, 1)

        class MockReq:
            def __init__(self, c, u):
                self.cart = c
                self.user = u
                self.session = Client().session

        with self.assertRaises(ValidationError) as ctx:
            process_checkout(MockReq(cart, customer), {
                'full_name': 'Real Customer',
                'phone_number': 'ghdfsh',
                'address': 'Dhaka Bangladesh',
                'delivery_zone': 'DHAKA',
            })
        self.assertIn("সঠিক ১১ ডিজিটের বাংলাদেশি মোবাইল নম্বর দিন", str(ctx.exception))
